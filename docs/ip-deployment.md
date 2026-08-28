# Развёртывание по IP без домена

Эта инструкция — для одного администратора, который открывает панель напрямую по публичному IP-адресу сервера. Она намеренно использует HTTP без TLS и **не подходит** для публичного или многопользовательского сервиса.

Для запуска с доменом, HTTPS, автоматическими backup и мониторингом используйте [production.md](production.md).

## Что потребуется

- Ubuntu 24.04 LTS сервер с публичным IPv4;
- доступ к серверу по SSH с `sudo`;
- доступ к DNS/VK не требуется, если домен не используется;
- токен сообщества VK и числовой ID сообщества.

В Cloud.ru перед запуском добавьте правило группы безопасности: входящий TCP-трафик на порт `80` от `0.0.0.0/0`. Группа должна быть привязана к сетевому интерфейсу ВМ.

## 1. Установите Docker

Выполняйте команды на сервере по одной:

```shell
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Выйдите из SSH (`exit`) и подключитесь снова. Проверьте установку:

```shell
docker compose version
```

Если Ubuntu просит перезагрузку, сделайте это до первого запуска:

```shell
sudo reboot
```

## 2. Подготовьте проект и настройки

На сервере проект должен находиться в `/opt/vk-tutors-bot`:

```shell
sudo mv ~/vk-tutors-bot /opt/vk-tutors-bot
sudo chown -R "$USER:$USER" /opt/vk-tutors-bot
cd /opt/vk-tutors-bot
cp .env.production.example .env.production
chmod 600 .env.production
```

Если файл `.env.production` уже создан, не копируйте его повторно.

Для HTTP-режима откройте `.env.production` и установите:

```ini
APP_ENV=development
SESSION_COOKIE_SECURE=false
APP_PORT=80
```

Заполните остальные обязательные значения:

```ini
POSTGRES_PASSWORD=<первый_случайный_пароль>
DATABASE_URL=postgresql+asyncpg://vk_tutors:<первый_случайный_пароль>@postgres:5432/vk_tutors
ADMIN_BOOTSTRAP_USERNAME=admin
ADMIN_BOOTSTRAP_PASSWORD=<второй_случайный_пароль>
VK_GROUP_ID=<числовой_ID_сообщества>
VK_ACCESS_TOKEN=<токен_сообщества>
```

Создайте каждый пароль отдельной командой:

```shell
openssl rand -hex 32
```

`DOMAIN` и `HEALTHCHECK_URL` в этом режиме не используются. Не добавляйте `.env.production` в Git и не передавайте его содержимое.

## 3. Первый запуск

Не используйте `compose.prod.yaml`: он включает Caddy и требует домен.

```shell
cd /opt/vk-tutors-bot
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml config -q
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml up -d --build
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml ps
```

В последней команде `postgres`, `api` и `frontend` должны получить статус `healthy`; `vk-listener` и `worker` — `running`. Одноразовый контейнер `migrate` после применения миграций завершится — это нормально.

Откройте в браузере:

```text
http://<публичный_IP_сервера>
```

Войдите с `ADMIN_BOOTSTRAP_USERNAME` и `ADMIN_BOOTSTRAP_PASSWORD` из `.env.production`.

## 4. Если панель не открывается

1. Убедитесь, что в адресе браузера указан `http://`, не `https://`.
2. В Cloud.ru откройте **Сеть → Группы безопасности**, выберите группу с подключённым интерфейсом сервера и добавьте входящее правило: TCP, порт `80`, источник `0.0.0.0/0`.
3. На сервере проверьте контейнеры:

   ```shell
   cd /opt/vk-tutors-bot
   ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml ps
   curl -i http://localhost/health
   ```

   Последняя команда должна вернуть `HTTP/1.1 200 OK` и `ok`.

4. Посмотрите журналы нужного сервиса:

   ```shell
   ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml logs --tail=100 frontend api vk-listener worker
   ```

## 5. Проверка VK

В настройках сообщества VK включите Bots Long Poll и событие `message_new`, добавьте сообщество в тестовую беседу и отправьте там новое сообщение. После этого беседа должна появиться в панели. Создайте тестовую учебную группу, привяжите к ней беседу и сделайте тестовую рассылку.

## 6. Обновление после нового commit

Сначала проверьте, что локальных изменений на сервере нет:

```shell
cd /opt/vk-tutors-bot
git status --short
```

Если команда ничего не вывела, обновите код и контейнеры:

```shell
git pull --ff-only
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml up -d --build
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml ps
```

Не используйте `docker compose down -v`: эта команда удаляет volume с PostgreSQL и загруженными изображениями.

## Ограничения этого режима

- нет HTTPS, поэтому браузер передаёт пароль администратора по HTTP;
- нет systemd-мониторинга и автоматических backup из production-конфигурации;
- не используйте этот вариант при доступе нескольких людей или из недоверенной сети.

Контейнеры настроены с `restart: unless-stopped`, поэтому после перезагрузки сервера Docker автоматически вернёт долгоживущие сервисы. Всё равно держите отдельную резервную копию PostgreSQL и медиафайлов.
