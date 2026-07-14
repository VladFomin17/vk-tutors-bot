import { HttpError, type DataProvider } from "react-admin";

async function api(path: string, init?: RequestInit) {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers: init?.body === undefined ? undefined : { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new HttpError(body.detail ?? "Ошибка запроса", response.status, body);
  }
  return response.status === 204 ? undefined : response.json();
}

function unsupported(): never {
  throw new Error("Operation is not supported");
}

export const dataProvider: DataProvider = {
  getList: async (resource, params) => {
    let path: string;
    if (resource === "study_groups") {
      path = "/study-groups";
    } else if (resource === "broadcasts") {
      path = "/broadcasts";
    } else if (resource === "broadcast_results" && params.filter.broadcast_id) {
      path = `/broadcasts/${params.filter.broadcast_id}/results`;
    } else if (resource === "vk_chats") {
      path = "/vk-chats";
    } else if (resource === "chat_members" && params.filter.chat_id) {
      path = `/vk-chats/${params.filter.chat_id}/members`;
    } else {
      return unsupported();
    }
    const data = await api(path);
    return { data, total: data.length };
  },
  create: async (resource, params) => {
    if (resource !== "study_groups" && resource !== "broadcasts") {
      return unsupported();
    }
    const data = await api(resource === "study_groups" ? "/study-groups" : "/broadcasts", {
      method: "POST",
      body: JSON.stringify(params.data),
    });
    return { data };
  },
  update: async (resource, params) => {
    let path: string;
    let body: object;
    if (resource === "vk_chats") {
      path = `/vk-chats/${params.id}`;
      body = { study_group_id: params.data.study_group_id ?? null };
    } else if (resource === "chat_members") {
      path = `/vk-chats/${params.data.chat_id}/members/${params.data.vk_user_id}`;
      body = { role: params.data.role };
    } else {
      return unsupported();
    }
    const data = await api(path, { method: "PATCH", body: JSON.stringify(body) });
    return { data: { ...params.data, ...data } };
  },
  getOne: async () => unsupported(),
  getMany: async () => unsupported(),
  getManyReference: async () => unsupported(),
  updateMany: async () => unsupported(),
  delete: async () => unsupported(),
  deleteMany: async () => unsupported(),
};
