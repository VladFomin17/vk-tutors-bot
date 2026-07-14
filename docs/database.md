# Database

Все даты хранятся в PostgreSQL как `timestamp with time zone` в UTC.

```mermaid
erDiagram
    STUDY_GROUP ||--o| VK_CHAT : "назначена"
    VK_CHAT ||--o{ CHAT_MEMBER : "содержит"
    VK_USER ||--o{ CHAT_MEMBER : "состоит"

    STUDY_GROUP {
        bigint id PK
        varchar name UK
        boolean is_active
    }
    VK_CHAT {
        bigint id PK
        bigint peer_id UK
        bigint study_group_id FK,UK
        varchar title
        boolean is_active
    }
    VK_USER {
        bigint vk_user_id PK
        varchar first_name
        varchar last_name
    }
    CHAT_MEMBER {
        bigint chat_id PK,FK
        bigint vk_user_id PK,FK
        varchar role
        boolean is_active
        timestamptz first_seen_at
        timestamptz last_seen_at
    }
```

- `vk_chats` создаётся при обнаружении события VK и позднее связывается с одной учебной группой.
- Составной ключ `chat_members` не допускает повторного членства пользователя в одной беседе.
- `role`: `unknown`, `student`, `tutor` или `leader`. Новые участники получают `unknown` до классификации.
