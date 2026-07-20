# VK Tutors Bot

Production-сервис для рассылок и сбора подтверждений в VK-беседах учебных групп. В состав входят FastAPI, PostgreSQL, VK Long Poll listener, APScheduler worker и административная панель React Admin.

## Локальная разработка

Требования: Docker Engine с Compose v2 и свободный порт 80.

```shell
cp .env.example .env
# заполните ADMIN_BOOTSTRAP_PASSWORD, VK_GROUP_ID и VK_ACCESS_TOKEN
docker compose up --build
```

Панель: `http://localhost`. Readiness: `http://localhost/api/v1/health/ready`.

Проверки:

```shell
docker build --target test -t vk-tutors-backend-test ./backend
docker run --rm vk-tutors-backend-test
cd frontend && npm ci && npm test && npm run build
```

## Документация

- [Production-развёртывание и эксплуатация](docs/production.md): домен, HTTPS, секреты, systemd, backup/restore, мониторинг и диагностика.
- [Руководство администратора](docs/admin-guide.md): подключение VK-беседы, группы, участники, рассылки и результаты.
- [Архитектура](docs/architecture.md) и [схема данных](docs/database.md).
- [Проверка VK API](docs/vk-spike.md).

Версия: **1.0.0**.
