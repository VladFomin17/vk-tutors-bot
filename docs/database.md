# Database

Все даты хранятся в PostgreSQL как `timestamp with time zone` в UTC.

```mermaid
erDiagram
    STUDY_GROUP ||--o| VK_CHAT : "назначена"
    VK_CHAT ||--o{ CHAT_MEMBER : "содержит"
    VK_USER ||--o{ CHAT_MEMBER : "состоит"
    BROADCAST ||--|{ BROADCAST_TARGET : "адресована"
    STUDY_GROUP ||--o{ BROADCAST_TARGET : "выбрана"
    VK_CHAT ||--o{ BROADCAST_TARGET : "получает"
    BROADCAST_TARGET ||--|{ BROADCAST_RECIPIENT : "фиксирует"
    VK_USER ||--o{ BROADCAST_RECIPIENT : "получатель"
    BROADCAST_TARGET ||--|{ OUTBOUND_MESSAGE : "порождает"
    BROADCAST_TARGET ||--o{ BROADCAST_RESPONSE : "получает"
    OUTBOUND_MESSAGE ||--o{ BROADCAST_RESPONSE : "цитируется"
    VK_USER ||--o{ BROADCAST_RESPONSE : "отвечает"

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
    BROADCAST {
        bigint id PK
        varchar title
        text message_text
        varchar link
        timestamptz deadline
        varchar confirmation_type
    }
    BROADCAST_TARGET {
        bigint id PK
        bigint broadcast_id FK
        bigint study_group_id FK
        bigint chat_id FK
    }
    BROADCAST_RECIPIENT {
        bigint target_id PK,FK
        bigint vk_user_id PK,FK
    }
    OUTBOUND_MESSAGE {
        bigint id PK
        bigint target_id FK
        varchar kind
        varchar status
        timestamptz scheduled_at
        integer random_id
        varchar broadcast_token UK
    }
    BROADCAST_RESPONSE {
        bigint id PK
        bigint target_id FK
        bigint outbound_message_id FK
        bigint vk_user_id FK
        bigint peer_id
        bigint vk_message_id
        bigint conversation_message_id
        text text
        jsonb attachments
        timestamptz responded_at
        boolean is_late
    }
```

- `vk_chats` создаётся при обнаружении события VK и позднее связывается с одной учебной группой.
- Составной ключ `chat_members` не допускает повторного членства пользователя в одной беседе.
- `role`: `unknown`, `student`, `tutor` или `leader`. Новые участники получают `unknown` до классификации.
- `broadcast_recipients` хранит неизменяемый снимок активных первокурсников на момент создания рассылки.
- `outbound_messages` является PostgreSQL outbox: начальная отправка планируется сразу, напоминание — за 24 часа до дедлайна, если этот момент ещё не прошёл.
- `broadcast_responses` хранит первую подходящую reply-попытку каждого получателя; уникальный `(peer_id, conversation_message_id)` делает обработку Long Poll идемпотентной.
