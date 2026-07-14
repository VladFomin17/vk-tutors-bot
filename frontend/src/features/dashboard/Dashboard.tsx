import { type FormEvent, useState } from "react";
import { useCreate, useGetList, useNotify, useUpdate } from "react-admin";

import { BroadcastsPanel } from "../broadcasts/BroadcastsPanel";

type StudyGroup = { id: number; name: string; is_active: boolean };
type VkChat = {
  id: number;
  peer_id: number;
  title: string | null;
  study_group_id: number | null;
  is_active: boolean;
};
type ChatMember = {
  id: string;
  chat_id: number;
  vk_user_id: number;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
};

const roleLabels: Record<string, string> = {
  unknown: "Не классифицирован",
  student: "Первокурсник",
  tutor: "Тьютор",
  leader: "Руководитель",
};

export function Dashboard() {
  const notify = useNotify();
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const { data: groups = [] } = useGetList<StudyGroup>("study_groups");
  const { data: chats = [] } = useGetList<VkChat>("vk_chats");
  const { data: members = [] } = useGetList<ChatMember>(
    "chat_members",
    { filter: { chat_id: selectedChatId } },
    { enabled: selectedChatId !== null },
  );
  const [createGroup, { isPending: isCreating }] = useCreate();
  const [updateRecord] = useUpdate();

  function submitGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const name = String(new FormData(form).get("name") ?? "");
    createGroup(
      "study_groups",
      { data: { name } },
      {
        onSuccess: () => {
          form.reset();
          notify("Учебная группа создана", { type: "success" });
        },
        onError: () => notify("Не удалось создать группу", { type: "error" }),
      },
    );
  }

  return (
    <main>
      <h1>Настройка учебных групп</h1>

      <section>
        <h2>Учебные группы</h2>
        <form onSubmit={submitGroup}>
          <label>
            Название группы{" "}
            <input name="name" required maxLength={64} />
          </label>{" "}
          <button disabled={isCreating} type="submit">
            Создать
          </button>
        </form>
      </section>

      <section>
        <h2>Обнаруженные беседы</h2>
        {chats.length === 0 ? <p>Беседы пока не обнаружены.</p> : null}
        {chats.map((chat) => (
          <article key={chat.id}>
            <strong>{chat.title ?? `Беседа ${chat.id}`}</strong>{" "}
            <label>
              Учебная группа{" "}
              <select
                key={`${chat.id}:${chat.study_group_id}`}
                defaultValue={chat.study_group_id ?? ""}
                onChange={(event) =>
                  updateRecord(
                    "vk_chats",
                    {
                      id: chat.id,
                      data: { study_group_id: Number(event.target.value) || null },
                      previousData: chat,
                    },
                    {
                      mutationMode: "pessimistic",
                      onSuccess: () => notify("Привязка сохранена", { type: "success" }),
                      onError: () =>
                        notify("Не удалось сохранить привязку", { type: "error" }),
                    },
                  )
                }
              >
                <option value="">Не назначена</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </label>{" "}
            <button type="button" onClick={() => setSelectedChatId(chat.id)}>
              Участники
            </button>
          </article>
        ))}
      </section>

      {selectedChatId !== null ? (
        <section>
          <h2>Участники беседы</h2>
          {members.length === 0 ? <p>Участники не найдены.</p> : null}
          <table>
            <thead>
              <tr>
                <th>Имя</th>
                <th>Роль</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.id}>
                  <td>
                    {`${member.last_name} ${member.first_name}`}
                    {member.is_active ? "" : " (не в беседе)"}
                  </td>
                  <td>
                    <select
                      key={`${member.id}:${member.role}`}
                      defaultValue={member.role}
                      onChange={(event) =>
                        updateRecord(
                          "chat_members",
                          {
                            id: member.id,
                            data: { ...member, role: event.target.value },
                            previousData: member,
                          },
                          {
                            mutationMode: "pessimistic",
                            onSuccess: () => notify("Роль сохранена", { type: "success" }),
                            onError: () =>
                              notify("Не удалось сохранить роль", { type: "error" }),
                          },
                        )
                      }
                    >
                      {Object.entries(roleLabels).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <BroadcastsPanel
        groups={groups}
        linkedGroupIds={new Set(chats.flatMap((chat) => chat.study_group_id ?? []))}
      />
    </main>
  );
}
