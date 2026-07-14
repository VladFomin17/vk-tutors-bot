import RefreshIcon from "@mui/icons-material/Refresh";
import { Alert, Button } from "@mui/material";

export function QueryErrorState({
  message = "Не удалось загрузить данные.",
  onRetry,
}: {
  message?: string;
  onRetry: () => void | Promise<unknown>;
}) {
  return (
    <Alert
      action={<Button color="inherit" onClick={() => void onRetry()} size="small" startIcon={<RefreshIcon />}>Повторить</Button>}
      severity="error"
    >
      {message}
    </Alert>
  );
}
