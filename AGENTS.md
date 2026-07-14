# AGENTS.md

## Project Overview

This project is a production-quality VK bot and administrative panel for automating tutor communications with first-year university students.

The goal is to reduce manual work related to survey distribution and response collection while keeping the system simple, maintainable, and easy to extend.

This is **not** a throwaway prototype. Every implementation should assume long-term maintenance.

---

# Core Principles

- Prioritize maintainability over clever solutions.
- Simplicity is preferred over unnecessary abstractions.
- Think like a senior software engineer.
- Challenge requirements if a significantly better engineering solution exists.
- Explain architectural decisions before implementing them.
- Minimize technical debt.
- Avoid premature optimization.

When requirements conflict, optimize for:

1. Simplicity
2. Maintainability
3. Readability
4. Reliability
5. Performance

---

# Technology Stack

## Backend

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic v2
- APScheduler

## Frontend

- React
- TypeScript
- Vite
- React Admin
- React Query
- React Hook Form

## Infrastructure

- Docker
- Docker Compose

---

# Architecture

Use a modular architecture.

Separate responsibilities clearly.

Example structure:

backend/
├── api/
├── core/
├── db/
├── models/
├── repositories/
├── services/
├── schemas/
├── integrations/
│   └── vk/
├── scheduler/
└── utils/

frontend/
├── src/
│   ├── pages/
│   ├── features/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   ├── types/
│   ├── layouts/
│   └── utils/

Never create "god modules".

---

# Code Style

Write code that another developer can understand in six months.

Prefer explicit code over clever code.

Always:

- use meaningful names
- use type hints
- keep functions small
- keep classes focused
- avoid nested logic
- avoid duplicated code
- avoid magic values

Never:

- leave commented-out code
- leave dead code
- suppress warnings without explanation
- use one-letter variable names except trivial loops

---

# Backend Guidelines

Prefer:

- async endpoints
- dependency injection
- service layer
- clear separation of API/business/database

Repositories should only exist when they actually reduce complexity.

Do not create unnecessary abstraction layers.

Use SQLAlchemy 2.x idioms.

Keep business logic outside API routes.

---

# Frontend Guidelines

The admin panel is an internal tool.

Prioritize usability over visual appearance.

Prefer:

- reusable components
- feature-based organization
- typed API layer
- custom hooks for business logic

Avoid:

- duplicated state
- prop drilling
- oversized components

Prefer composition over inheritance.

---

# Database

Database design should be normalized.

Prefer clean relationships.

Avoid duplicated data unless there is a measurable benefit.

Always create Alembic migrations.

---

# VK Integration

Use the official VK API.

Keep all VK-related logic isolated inside dedicated integration modules.

Never mix VK API calls with business logic.

Store:

- VK user IDs
- message IDs
- attachments
- timestamps

---

# Scheduling

Use APScheduler.

Scheduled jobs must be idempotent whenever possible.

Avoid duplicated executions.

Log every scheduled task.

---

# Error Handling

Never silently ignore exceptions.

Always:

- log unexpected errors
- return meaningful API responses
- avoid leaking internal details

Use custom exception types when appropriate.

---

# Logging

Use structured logging.

Log important events:

- broadcast creation
- message delivery
- incoming responses
- scheduler execution
- export generation
- authentication events

Avoid excessive logging.

---

# Security

Never commit:

- .env
- secrets
- API tokens
- passwords
- generated files

Validate all external input.

Never trust client data.

---

# Dependencies

Before adding a dependency:

Explain:

- why it is needed
- why existing tools cannot solve the problem

Avoid dependency bloat.

---

# Documentation

Keep documentation updated.

Maintain:

- README.md
- CHANGELOG.md
- architecture documentation
- API documentation
- environment variables

Documentation should evolve together with the code.

---

# Git Workflow

Treat this as a professional repository.

Always:

- make small commits
- keep commits focused
- use Conventional Commits

Examples:

feat:
fix:
refactor:
docs:
test:
chore:

Never mix unrelated changes.

After each completed task:

- suggest a commit message
- summarize changes
- mention updated documentation

---

# Docker

The project must always be runnable through Docker Compose.

A fresh clone should require only:

docker compose up

No manual environment setup should be necessary beyond configuring environment variables.

---

# Code Review

After every completed feature:

Perform a self-review.

Look for:

- duplicated code
- poor naming
- unnecessary abstractions
- architecture problems
- security concerns
- maintainability issues

Refactor immediately if improvements are obvious.

---

# Development Workflow

For every task:

1. Analyze requirements.
2. Explain the approach.
3. Explain architectural decisions.
4. Implement.
5. Review.
6. Refactor if necessary.
7. Update documentation.
8. Suggest a commit.

Never jump directly into coding complex features.

---

# Project Philosophy

This project should feel like it was written by an experienced software engineer.

Every decision should improve one or more of:

- readability
- maintainability
- simplicity
- extensibility
- reliability

If a better engineering solution exists than the requested one:

Stop.

Explain the tradeoffs.

Recommend the better solution before implementing.

---

# Important

Prefer boring, predictable, maintainable code over clever code.

Good architecture is more valuable than fewer lines of code.

The repository should always be clean enough that it can be published to GitHub without additional cleanup.