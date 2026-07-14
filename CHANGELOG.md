# Changelog

## Unreleased

### Added

- Initial FastAPI, Alembic, PostgreSQL and React Admin scaffold.
- Docker Compose development runtime.
- VK API feasibility spike and architecture documentation.
- Study group, VK chat, VK user and chat membership database schema.
- VK Long Poll listener with idempotent chat and member synchronization.
- Single-administrator authentication with revocable database sessions.
- Protected study group, VK chat linking and member role management.
- Broadcast creation, recipient snapshots and transactional PostgreSQL outbox jobs.
- APScheduler worker for idempotent VK delivery and deadline-safe reminders.
- Idempotent reply confirmation capture and per-student results in the admin panel.
- XLSX and DOCX broadcast result exports.

### Fixed

- Fixed broadcast results failing to load when the recipient snapshot was not empty.
- Simplified DOCX exports to group headings and respondent surnames.
- Allow students to replace an earlier confirmation with a newer valid reply.
- Empty React Admin screen caused by missing resource registration.
- VK chat titles are restored for chats discovered through Long Poll.
- Broadcasts can be created for test chats without classified students.
