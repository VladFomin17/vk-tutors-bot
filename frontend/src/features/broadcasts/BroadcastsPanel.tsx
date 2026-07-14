import { type FormEvent, useState } from "react";
import { useCreate, useGetList, useNotify } from "react-admin";

type StudyGroup = { id: number; name: string; is_active: boolean };
type Broadcast = {
  id: number;
  title: string;
  deadline: string;
  confirmation_type: "any_message" | "image";
  target_count: number;
  recipient_count: number;
};
type BroadcastResult = {
  id: string;
  study_group_name: string;
  vk_user_id: number;
  first_name: string;
  last_name: string;
  responded: boolean;
  text: string | null;
  attachments: Array<{
    type?: string;
    photo?: { sizes?: Array<{ url?: string }> };
  }>;
  media: Array<{ id: number; content_type: string; size_bytes: number }>;
  responded_at: string | null;
  is_late: boolean | null;
};

type BroadcastsPanelProps = {
  groups: StudyGroup[];
  linkedGroupIds: Set<number>;
};

export function BroadcastsPanel({ groups, linkedGroupIds }: BroadcastsPanelProps) {
  const notify = useNotify();
  const [selectedBroadcastId, setSelectedBroadcastId] = useState<number | null>(null);
  const [createBroadcast, { isPending }] = useCreate();
  const { data: broadcasts = [] } = useGetList<Broadcast>("broadcasts");
  const { data: results = [] } = useGetList<BroadcastResult>(
    "broadcast_results",
    { filter: { broadcast_id: selectedBroadcastId } },
    { enabled: selectedBroadcastId !== null },
  );
  const availableGroups = groups.filter((group) => linkedGroupIds.has(group.id));

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const studyGroupIds = values.getAll("study_group_ids").map(Number);
    if (studyGroupIds.length === 0) {
      notify("Выберите хотя бы одну учебную группу", { type: "warning" });
      return;
    }
    createBroadcast(
      "broadcasts",
      {
        data: {
          title: values.get("title"),
          message_text: values.get("message_text"),
          link: values.get("link") || null,
          deadline: new Date(String(values.get("deadline"))).toISOString(),
          confirmation_type: values.get("confirmation_type"),
          study_group_ids: studyGroupIds,
        },
      },
      {
        onSuccess: () => {
          form.reset();
          notify("Рассылка создана и поставлена в очередь", { type: "success" });
        },
        onError: (error) =>
          notify(error instanceof Error ? error.message : "Не удалось создать рассылку", {
            type: "error",
          }),
      },
    );
  }

  return (
    <section>
      <h2>Новая рассылка</h2>
      <form onSubmit={submit}>
        <p>
          <label>
            Название <input name="title" required maxLength={128} />
          </label>
        </p>
        <p>
          <label>
            Текст сообщения <textarea name="message_text" required maxLength={10000} />
          </label>
        </p>
        <p>
          <label>
            Ссылка на опрос (необязательно){" "}
            <input name="link" type="url" maxLength={2048} placeholder="https://..." />
          </label>
        </p>
        <p>
          <label>
            Дедлайн <input name="deadline" type="datetime-local" required />
          </label>
        </p>
        <p>
          <label>
            Подтверждение{" "}
            <select name="confirmation_type" defaultValue="any_message">
              <option value="any_message">Любое сообщение</option>
              <option value="image">Изображение</option>
            </select>
          </label>
        </p>
        <fieldset>
          <legend>Учебные группы</legend>
          {availableGroups.length === 0 ? <p>Сначала привяжите беседу к учебной группе.</p> : null}
          {availableGroups.map((group) => (
            <label key={group.id}>
              <input name="study_group_ids" type="checkbox" value={group.id} /> {group.name}{" "}
            </label>
          ))}
        </fieldset>
        <p>
          <button disabled={isPending || availableGroups.length === 0} type="submit">
            Создать рассылку
          </button>
        </p>
      </form>

      <h2>История рассылок</h2>
      {broadcasts.length === 0 ? <p>Рассылок пока нет.</p> : null}
      {broadcasts.map((broadcast) => (
        <article key={broadcast.id}>
          <strong>{broadcast.title}</strong> — групп: {broadcast.target_count}, получателей:{" "}
          {broadcast.recipient_count}, дедлайн: {new Date(broadcast.deadline).toLocaleString("ru-RU")}{" "}
          <button type="button" onClick={() => setSelectedBroadcastId(broadcast.id)}>
            Результаты
          </button>
        </article>
      ))}

      {selectedBroadcastId !== null ? (
        <section>
          <h3>Результаты рассылки</h3>
          <p>
            <a href={`/api/v1/broadcasts/${selectedBroadcastId}/export.xlsx`}>Скачать XLSX</a>{" "}
            <a href={`/api/v1/broadcasts/${selectedBroadcastId}/export.docx`}>Скачать DOCX</a>
          </p>
          {results.length === 0 ? <p>В снимке рассылки нет студентов.</p> : null}
          <table>
            <thead>
              <tr>
                <th>Группа</th>
                <th>Студент</th>
                <th>Статус</th>
                <th>Ответ</th>
                <th>Вложения</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.id}>
                  <td>{result.study_group_name}</td>
                  <td>{`${result.last_name} ${result.first_name}`}</td>
                  <td>
                    {result.responded
                      ? `Ответил${result.is_late ? " после дедлайна" : ""}`
                      : "Не ответил"}
                  </td>
                  <td>
                    {result.text ?? ""}
                    {result.responded_at
                      ? ` (${new Date(result.responded_at).toLocaleString("ru-RU")})`
                      : ""}
                  </td>
                  <td>
                    {resultImageUrls(result).map((url, index) => (
                      <a key={url} href={url} target="_blank" rel="noreferrer">
                        Изображение {index + 1}{" "}
                      </a>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </section>
  );
}

function imageUrl(attachment: BroadcastResult["attachments"][number]): string[] {
  if (attachment.type !== "photo") {
    return [];
  }
  const sizes = attachment.photo?.sizes ?? [];
  const url = sizes[sizes.length - 1]?.url;
  return url ? [url] : [];
}

function resultImageUrls(result: BroadcastResult): string[] {
  if (result.media.length > 0) {
    return result.media.map((media) => `/api/v1/response-media/${media.id}`);
  }
  return result.attachments.flatMap(imageUrl);
}
