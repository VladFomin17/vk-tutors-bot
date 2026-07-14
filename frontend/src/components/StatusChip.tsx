import { Chip } from "@mui/material";

import { isBroadcastCompleted } from "../utils/broadcasts";

export function BroadcastStatusChip({ deadline }: { deadline: string }) {
  const completed = isBroadcastCompleted(deadline);
  return (
    <Chip
      color={completed ? "default" : "success"}
      label={completed ? "Завершена" : "Активна"}
      size="small"
      variant={completed ? "outlined" : "filled"}
    />
  );
}
