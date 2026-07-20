# Production-развёртывание и эксплуатация

## Рекомендуемый сервер

Для 20 групп по 20 человек (около 400 студентов), одного администратора и обычных рассылок достаточно одного x86_64 Linux-сервера:

- 2 vCPU;
- 4 ГБ RAM;
- 30 ГБ SSD/NVMe;
- Ubuntu 24.04 LTS или другой поддерживаемый Linux;
- публичный IPv4, домен и открытые TCP 80/443, UDP 443;
- отдельное внешнее хранилище резервных копий.

Нагрузка определяется главным образом количеством и размером изображений. Выделяйте дополнительно объём их хранения × 2 для локальной рабочей копии и временного backup. Переходите на 4 vCPU/8 ГБ RAM только при измеренном дефиците CPU/RAM; на S3-совместимое хранилище — когда одного сервера или его диска недостаточно.

## Подготовка домена и хоста

1. Создайте DNS `A`-запись домена, например `admin.example.ru`, на IP сервера. До запуска проверьте `dig +short admin.example.ru`.
2. Установите Docker Engine и Compose plugin из официального репозитория Docker. Выполните `sudo systemctl enable --now docker` и проверьте `docker compose version`.
3. Разрешите входящие 22/tcp только с доверенных адресов, 80/tcp, 443/tcp и 443/udp. PostgreSQL наружу не публикуется.
4. Разместите репозиторий в `/opt/vk-tutors-bot` и ограничьте доступ к нему администратором сервера.

## Production-секреты

```shell
cd /opt/vk-tutors-bot
cp .env.production.example .env.production
openssl rand -hex 32
openssl rand -hex 32
chmod 600 .env.production
```

Первое значение используйте одновременно в `POSTGRES_PASSWORD` и в пароле `DATABASE_URL`, второе — в `ADMIN_BOOTSTRAP_PASSWORD`. Заполните `DOMAIN`, `HEALTHCHECK_URL`, `VK_GROUP_ID` и `VK_ACCESS_TOKEN`. Не пересылайте файл и не помещайте его в Git; храните зашифрованную копию отдельно. `APP_ENV=production` заставляет приложение отклонить короткие пароли, небезопасную cookie, отсутствующие VK-реквизиты и известные dev-пароли.

При компрометации замените VK token в настройках сообщества, оба пароля в `.env.production`, измените `SESSION_COOKIE_NAME` и пересоздайте контейнеры. Пароль PostgreSQL в существующем volume меняйте командой `ALTER ROLE`, а не только правкой `.env.production`.

## Первый запуск

```shell
cd /opt/vk-tutors-bot
chmod 750 deploy/*.sh
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml -f compose.prod.yaml config
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml -f compose.prod.yaml build
sudo cp deploy/systemd/vk-tutors* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vk-tutors.service vk-tutors-backup.timer vk-tutors-monitor.timer
```

Caddy автоматически получает и обновляет TLS-сертификат. Проверьте:

```shell
curl --fail https://admin.example.ru/api/v1/health/ready
sudo systemctl status vk-tutors.service vk-tutors-backup.timer vk-tutors-monitor.timer
```

После перезагрузки `vk-tutors.service` запускает Compose, а `restart: unless-stopped` возвращает упавшие долгоживущие контейнеры. Для обновления кода выполните backup, `git pull`, команды `build` и `systemctl restart vk-tutors.service`.

## Логи и контроль состояния

Docker хранит не более пяти файлов по 10 МБ на контейнер. Просмотр:

```shell
ENV_FILE=.env.production docker compose --env-file .env.production -f compose.yaml -f compose.prod.yaml logs --since 30m api vk-listener worker
journalctl -u vk-tutors-monitor.service -u vk-tutors-backup.service --since today
```

Раз в две минуты monitor проверяет:

- заполнение файловой системы (`DISK_USAGE_LIMIT`, по умолчанию 85%);
- запущены ли `postgres`, `api`, `vk-listener`, `worker`, `frontend`, `caddy`;
- публичный readiness, включая соединение API с PostgreSQL.

Ошибка видна как failed-запуск `vk-tutors-monitor.service` в journal. Дополнительно настройте внешний мониторинг `HEALTHCHECK_URL`: локальная проверка не обнаружит потерю питания, сети или всего хоста. Для уведомлений без дополнительного стека используйте возможности мониторинга вашего хостинга на failed systemd unit и заполнение диска.

## Резервное копирование

`vk-tutors-backup.timer` ежедневно создаёт `/var/backups/vk-tutors/<UTC-время>/` с:

- `postgres.dump` в custom-формате PostgreSQL;
- `media.tar.gz` с изображениями;
- `SHA256SUMS`.

Каждая копия проверяется по SHA-256, чтением tar и реальным `pg_restore` во временную БД; временная БД после проверки удаляется. Локальные копии старше `BACKUP_RETENTION_DAYS` (14 дней) удаляются. Запуск вручную:

```shell
sudo /opt/vk-tutors-bot/deploy/backup.sh
sudo /opt/vk-tutors-bot/deploy/verify-backup.sh /var/backups/vk-tutors/20260720T031500Z
```

После создания синхронизируйте каталог на отдельный сервер/зашифрованное объектное хранилище средствами хостинга. Копия на том же диске не защищает от отказа диска или удаления VM. Ежедневно контролируйте статус timer, ежемесячно выполняйте тестовое восстановление на отдельном хосте.

## Проверенное восстановление

Скрипт проверяет SHA-256, останавливает приложение, пересоздаёт БД, восстанавливает PostgreSQL и изображения, запускает сервисы и ждёт публичный readiness. Это разрушительная операция: текущие БД и изображения заменяются выбранной копией.

```shell
sudo systemctl stop vk-tutors-backup.timer vk-tutors-monitor.timer
cd /opt/vk-tutors-bot
sudo RESTORE_CONFIRM=restore-vk-tutors ./deploy/restore.sh /var/backups/vk-tutors/20260720T031500Z
sudo systemctl start vk-tutors-backup.timer vk-tutors-monitor.timer
```

После восстановления войдите в панель, откройте последнюю рассылку и её изображение, затем отправьте тестовую рассылку в тестовую беседу. Если домен тестового хоста отличается, перед запуском исправьте `DOMAIN`, `HEALTHCHECK_URL` и DNS.

## Диагностика

### HTTPS не выпускается

Проверьте DNS, доступность 80/443 извне и `docker compose ... logs caddy`. Не закрывайте порт 80: он используется ACME-проверкой и перенаправлением на HTTPS.

### Readiness возвращает 503

Проверьте `postgres` и `api`, затем совпадение `POSTGRES_PASSWORD` с паролем в `DATABASE_URL`. После смены пароля существующий volume PostgreSQL не меняет пароль автоматически — выполните `ALTER ROLE` либо восстановление в новый volume.

### Listener постоянно перезапускается

Смотрите `docker compose ... logs vk-listener`. Типичные причины: неверные `VK_GROUP_ID`/`VK_ACCESS_TOKEN`, выключенный Bots Long Poll, отсутствие события `message_new`, недостаточные права сообщества или недоступность VK API.

### Worker работает, но сообщения не уходят

Проверьте ошибки доставки на странице рассылки и логи worker. Исправьте VK-доступ и используйте ручной повтор только для окончательно неудачных заданий до дедлайна; сохранённый `random_id` защищает от дубля на стороне VK.

### Беседа или участники не появились

Добавьте сообщество в беседу и отправьте новое сообщение. Listener не может обнаружить беседу только по старой истории. Проверьте права токена на сообщения и Long Poll.

### Заканчивается диск

Проверьте `df -h`, `docker system df` и размер `/var/backups/vk-tutors`. Сначала перенесите подтверждённые backup наружу и удалите устаревшие копии. Не выполняйте `docker compose down -v`: команда удаляет БД и изображения.

### Backup или restore завершился ошибкой

Не используйте неполный каталог с суффиксом `.tmp`. Проверьте `SHA256SUMS`, свободное место и журнал. При ошибке restore повторите операцию с той же целой копией; приложение остаётся остановленным или unhealthy, пока данные не восстановлены полностью.
