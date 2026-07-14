import type { Broadcast } from "../types/entities.ts";

export type BroadcastSort = "created_desc" | "deadline_asc" | "deadline_desc" | "title_asc";

export function isBroadcastCompleted(deadline: string, now = Date.now()): boolean {
  return new Date(deadline).getTime() < now;
}

export function sortBroadcasts(broadcasts: Broadcast[], order: BroadcastSort): Broadcast[] {
  return [...broadcasts].sort((left, right) => {
    if (order === "deadline_asc") return Date.parse(left.deadline) - Date.parse(right.deadline);
    if (order === "deadline_desc") return Date.parse(right.deadline) - Date.parse(left.deadline);
    if (order === "title_asc") return left.title.localeCompare(right.title, "ru-RU");
    return Date.parse(right.created_at) - Date.parse(left.created_at);
  });
}
