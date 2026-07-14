import type { AuthProvider } from "react-admin";

async function request(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`/api/v1/auth/${path}`, {
    ...init,
    credentials: "same-origin",
    headers: init?.body === undefined ? undefined : { "Content-Type": "application/json" },
  });
}

export const authProvider: AuthProvider = {
  login: async ({ username, password }) => {
    const response = await request("login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      throw new Error(response.status === 503 ? "Вход не настроен" : "Неверный логин или пароль");
    }
  },
  logout: async () => {
    await request("logout", { method: "POST" });
  },
  checkAuth: async () => {
    const response = await request("session");
    if (!response.ok) {
      throw new Error("Требуется вход");
    }
  },
  checkError: async (error) => {
    if (error?.status === 401 || error?.status === 403) {
      throw error;
    }
  },
  getIdentity: async () => ({ id: "admin", fullName: "Руководитель" }),
  getPermissions: async () => "admin",
};
