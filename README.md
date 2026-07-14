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

Сервис включает PostgreSQL, Alembic, FastAPI, React Admin и VK Long Poll listener.
Listener обнаруживает беседы и идемпотентно синхронизирует их участников.

Архитектура описана в [`docs/architecture.md`](docs/architecture.md), результаты
проверки VK API — в [`docs/vk-spike.md`](docs/vk-spike.md), схема данных — в
[`docs/database.md`](docs/database.md).
