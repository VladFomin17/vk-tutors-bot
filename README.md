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
Административная панель защищена логином и HttpOnly-сессией. Перед входом задайте
`ADMIN_BOOTSTRAP_PASSWORD` в `.env`; при работе через HTTPS также установите
`SESSION_COOKIE_SECURE=true`.
В панели можно создать учебную группу, привязать обнаруженную VK-беседу и
классифицировать её участников.
После классификации первокурсников можно создать рассылку для одной или нескольких групп.
API атомарно сохраняет рассылку, снимок получателей и задания начальной отправки и напоминания.
Пустой снимок получателей допустим для тестовой отправки в привязанную беседу.

Архитектура описана в [`docs/architecture.md`](docs/architecture.md), результаты
проверки VK API — в [`docs/vk-spike.md`](docs/vk-spike.md), схема данных — в
[`docs/database.md`](docs/database.md).
