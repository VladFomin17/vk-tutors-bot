# VK Tutors Bot

Сервис автоматизации рассылок и сбора подтверждений в беседах учебных групп VK.

## Запуск

1. Скопируйте `.env.example` в `.env` и заполните секреты.
   Обязательно замените `POSTGRES_PASSWORD` и ту же часть `DATABASE_URL`.
2. Запустите:

   ```shell
   docker compose up --build
   ```

3. Откройте `http://localhost`.

API healthcheck: `http://localhost/api/v1/health/ready`.

## Текущий этап

Scaffold включает PostgreSQL, Alembic, FastAPI и React Admin. Worker и VK
listener будут добавлены вместе с первой миграцией бизнес-сущностей, чтобы не
запускать процессы, которые получают и теряют события без сохранения.

Архитектура описана в [`docs/architecture.md`](docs/architecture.md), результаты
проверки VK API — в [`docs/vk-spike.md`](docs/vk-spike.md).
