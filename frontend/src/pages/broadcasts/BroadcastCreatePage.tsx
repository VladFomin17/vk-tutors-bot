import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  Grid,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Title, useBlocker, useCreate, useGetList, useNotify } from "react-admin";
import { Link, useNavigate } from "react-router-dom";

import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { SectionCard } from "../../components/SectionCard";
import type { ConfirmationType, StudyGroup, VkChat } from "../../types/entities";
import { isBroadcastDraftDirty } from "../../utils/broadcasts";
import { tomorrowLocalDateTime } from "../../utils/date";

export function BroadcastCreatePage() {
  const notify = useNotify();
  const navigate = useNavigate();
  const { data: groups = [], isPending: groupsPending, error: groupsError, refetch: refetchGroups } = useGetList<StudyGroup>("study_groups");
  const { data: chats = [], error: chatsError, refetch: refetchChats } = useGetList<VkChat>("vk_chats");
  const [createBroadcast, { isPending }] = useCreate();
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [link, setLink] = useState("");
  const [initialDeadline] = useState(tomorrowLocalDateTime);
  const [deadline, setDeadline] = useState(initialDeadline);
  const [confirmationType, setConfirmationType] = useState<ConfirmationType>("any_message");
  const [selectedGroups, setSelectedGroups] = useState<StudyGroup[]>([]);
  const submittedRef = useRef(false);
  const isDirty = isBroadcastDraftDirty({ title, message, link, deadline, confirmationType, selectedGroupCount: selectedGroups.length }, initialDeadline);
  const blocker = useBlocker(isDirty && !submittedRef.current);
  const linkedGroupIds = new Set(chats.flatMap((chat) => chat.study_group_id ?? []));
  const availableGroups = groups.filter((group) => group.is_active && linkedGroupIds.has(group.id));

  useEffect(() => {
    function warnBeforeUnload(event: BeforeUnloadEvent) {
      if (!isDirty || submittedRef.current) return;
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [isDirty]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedGroups.length === 0) {
      notify("Выберите хотя бы одну учебную группу", { type: "warning" });
      return;
    }
    createBroadcast(
      "broadcasts",
      {
        data: {
          title,
          message_text: message,
          link: link || null,
          deadline: new Date(deadline).toISOString(),
          confirmation_type: confirmationType,
          study_group_ids: selectedGroups.map((group) => group.id),
        },
      },
      {
        onSuccess: (broadcast) => {
          submittedRef.current = true;
          notify("Рассылка создана и поставлена в очередь", { type: "success" });
          navigate(`/broadcasts/${broadcast.id}/show`);
        },
        onError: (error) => notify(error instanceof Error ? error.message : "Не удалось создать рассылку", { type: "error" }),
      },
    );
  }

  return (
    <Stack spacing={3}>
      <Title title="Создать рассылку" />
      <PageHeader title="Создать рассылку" description="Заполните сообщение, выберите группы и проверьте предпросмотр." />
      {groupsError || chatsError ? <QueryErrorState message="Не удалось загрузить учебные группы и беседы." onRetry={() => Promise.all([refetchGroups(), refetchChats()])} /> : null}
      <Box component="form" onSubmit={submit}>
        <Grid container spacing={3} sx={{ alignItems: "flex-start" }}>
          <Grid size={{ xs: 12, lg: 8 }}>
            <Stack spacing={3}>
              <SectionCard title="Основная информация" description="Название видно только в административной панели.">
                <Stack spacing={2.5}>
                  <TextField autoFocus fullWidth label="Название рассылки" slotProps={{ htmlInput: { maxLength: 128 } }} onChange={(event) => setTitle(event.target.value)} required value={title} />
                  <TextField fullWidth label="Текст сообщения" slotProps={{ htmlInput: { maxLength: 10000 } }} minRows={6} multiline onChange={(event) => setMessage(event.target.value)} required value={message} />
                  <TextField fullWidth helperText="Например, ссылка на форму или опрос." label="Ссылка (необязательно)" slotProps={{ htmlInput: { maxLength: 2048 } }} onChange={(event) => setLink(event.target.value)} type="url" value={link} />
                </Stack>
              </SectionCard>

              <SectionCard title="Подтверждение и дедлайн">
                <Stack spacing={3}>
                  <FormControl>
                    <FormLabel>Что считать подтверждением</FormLabel>
                    <RadioGroup onChange={(event) => setConfirmationType(event.target.value as ConfirmationType)} value={confirmationType}>
                      <FormControlLabel control={<Radio />} label="Любое сообщение" value="any_message" />
                      <FormControlLabel control={<Radio />} label="Изображение" value="image" />
                    </RadioGroup>
                  </FormControl>
                  <TextField
                    helperText="Время интерпретируется в часовом поясе этого устройства."
                    label="Дедлайн"
                    onChange={(event) => setDeadline(event.target.value)}
                    required
                    slotProps={{ inputLabel: { shrink: true } }}
                    type="datetime-local"
                    value={deadline}
                  />
                </Stack>
              </SectionCard>

              <SectionCard
                title="Учебные группы"
                description="Доступны только группы с подключённой VK-беседой."
                action={availableGroups.length > 0 ? <Button onClick={() => setSelectedGroups(availableGroups)} size="small">Выбрать все</Button> : null}
              >
                {availableGroups.length === 0 && !groupsPending ? <Alert severity="warning">Сначала привяжите VK-беседу к учебной группе.</Alert> : (
                  <Autocomplete
                    disableCloseOnSelect
                    getOptionLabel={(group) => group.name}
                    isOptionEqualToValue={(option, value) => option.id === value.id}
                    loading={groupsPending}
                    multiple
                    onChange={(_, value) => setSelectedGroups(value)}
                    options={availableGroups}
                    renderInput={(params) => <TextField {...params} label="Выберите группы" placeholder="Начните вводить название" />}
                    value={selectedGroups}
                  />
                )}
              </SectionCard>

              <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                <Button component={Link} startIcon={<ArrowBackIcon />} to="/broadcasts">Отмена</Button>
                <Button disabled={isPending || availableGroups.length === 0} startIcon={isPending ? <CircularProgress color="inherit" size={18} /> : <SendOutlinedIcon />} type="submit" variant="contained">
                  {isPending ? "Создаём…" : "Создать рассылку"}
                </Button>
              </Stack>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, lg: 4 }} sx={{ position: { lg: "sticky" }, top: { lg: 88 } }}>
            <SectionCard title="Предпросмотр">
              <Box sx={{ bgcolor: "#f0f2f5", borderRadius: 2, p: 2 }}>
                <Box sx={{ bgcolor: "background.paper", borderRadius: 2, p: 2, border: 1, borderColor: "divider" }}>
                  <Typography color="primary" sx={{ fontWeight: 650 }}>@all</Typography>
                  <Typography sx={{ mt: 1, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                    {message || "Текст сообщения появится здесь."}
                  </Typography>
                  {link ? <Typography color="primary" sx={{ mt: 1, overflowWrap: "anywhere" }}>{link}</Typography> : null}
                  <Divider sx={{ my: 2 }} />
                  <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                    <Chip label={confirmationType === "image" ? "Нужно изображение" : "Подойдёт любое сообщение"} size="small" />
                    <Chip label={`${selectedGroups.length} групп`} size="small" variant="outlined" />
                  </Stack>
                </Box>
              </Box>
            </SectionCard>
          </Grid>
        </Grid>
      </Box>
      <Dialog onClose={() => blocker.reset?.()} open={blocker.state === "blocked"}>
        <DialogTitle>Закрыть форму?</DialogTitle>
        <DialogContent><DialogContentText>Введённые данные не сохранятся. Рассылка ещё не создана.</DialogContentText></DialogContent>
        <DialogActions>
          <Button onClick={() => blocker.reset?.()}>Остаться</Button>
          <Button color="error" onClick={() => blocker.proceed?.()}>Закрыть без сохранения</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
