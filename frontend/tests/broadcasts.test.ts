import assert from "node:assert/strict";
import test from "node:test";

import { isBroadcastCompleted, sortBroadcasts } from "../src/utils/broadcasts.ts";
import type { Broadcast } from "../src/types/entities.ts";

const base: Broadcast = {
  id: 1,
  title: "Бета",
  message_text: "Текст",
  link: null,
  deadline: "2026-07-20T10:00:00Z",
  confirmation_type: "any_message",
  created_at: "2026-07-10T10:00:00Z",
  target_count: 1,
  recipient_count: 1,
};

test("broadcast status respects the deadline", () => {
  assert.equal(isBroadcastCompleted(base.deadline, Date.parse("2026-07-20T09:59:59Z")), false);
  assert.equal(isBroadcastCompleted(base.deadline, Date.parse("2026-07-20T10:00:01Z")), true);
});

test("broadcast sorting does not mutate API data", () => {
  const broadcasts = [base, { ...base, id: 2, title: "Альфа", deadline: "2026-07-15T10:00:00Z" }];
  assert.deepEqual(sortBroadcasts(broadcasts, "deadline_asc").map((item) => item.id), [2, 1]);
  assert.deepEqual(broadcasts.map((item) => item.id), [1, 2]);
});
