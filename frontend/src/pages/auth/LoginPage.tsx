import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState, type FormEvent } from "react";
import { useLogin, useNotify } from "react-admin";

export function LoginPage() {
  const login = useLogin();
  const notify = useNotify();
  const [isPending, setIsPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setIsPending(true);
    try {
      await login({ username: values.get("username"), password: values.get("password") });
    } catch (error) {
      notify(error instanceof Error ? error.message : "Не удалось войти", { type: "error" });
      setIsPending(false);
    }
  }

  return (
    <Box component="main" sx={{ alignItems: "center", bgcolor: "background.default", display: "flex", minHeight: "100vh", justifyContent: "center", p: 2 }}>
      <Card variant="outlined" sx={{ maxWidth: 400, width: "100%" }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Stack spacing={1} sx={{ alignItems: "center", mb: 3, textAlign: "center" }}>
            <Avatar sx={{ bgcolor: "primary.main", height: 44, width: 44 }}><LockOutlinedIcon /></Avatar>
            <Typography component="h1" variant="h5">Панель руководителя</Typography>
            <Typography color="text.secondary" variant="body2">Управление рассылками тьюторского сектора</Typography>
          </Stack>
          <Stack component="form" onSubmit={submit} spacing={2.5}>
            <TextField autoComplete="username" autoFocus fullWidth label="Логин" name="username" required />
            <TextField autoComplete="current-password" fullWidth label="Пароль" name="password" required type="password" />
            <Button disabled={isPending} size="large" type="submit" variant="contained">
              {isPending ? <CircularProgress color="inherit" size={22} /> : "Войти"}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
