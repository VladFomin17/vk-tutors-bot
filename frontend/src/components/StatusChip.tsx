import { Chip } from "@mui/material";

export function BroadcastStatusChip({ deadline }: { deadline: string }) {
  const completed = new Date(deadline).getTime() < Date.now();
  return (
    <Chip
      color={completed ? "default" : "success"}
      label={completed ? "Завершена" : "Активна"}
      size="small"
      variant={completed ? "outlined" : "filled"}
    />
  );
}
