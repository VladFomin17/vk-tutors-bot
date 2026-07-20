# Changelog

## Unreleased

### Added

- Material UI dashboard layout with separate overview, broadcast, result and group pages.
- Search, filters, sorting, pagination, loading and empty states in the admin panel.
- Broadcast preview and in-app response image dialog.
- Localized administrator login and dependency-free frontend logic checks.
- Global student directory with group and activity filters.
- Authenticated aggregate statistics API and lazy-loaded MUI charts.
- Retryable frontend query errors and unsaved broadcast draft protection.
- Direct header logout and permanent broadcast deletion with media cleanup.
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
- Persistent, authenticated storage for VK response images.

### Fixed

- Fixed broadcast results failing to load when the recipient snapshot was not empty.
- Simplified DOCX exports to group headings and respondent surnames.
- Allow students to replace an earlier confirmation with a newer valid reply.
- Empty React Admin screen caused by missing resource registration.
- VK chat titles are restored for chats discovered through Long Poll.
- Broadcasts can be created for test chats without classified students.
