import AddIcon from "@mui/icons-material/Add";
import PeopleOutlineIcon from "@mui/icons-material/PeopleOutlined";
import {
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { useState, type FormEvent } from "react";
import { Title, useCreate, useGetList, useNotify, useUpdate } from "react-admin";
import { Link } from "react-router-dom";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { SectionCard } from "../../components/SectionCard";
import type { StudyGroup, VkChat } from "../../types/entities";

export function GroupListPage() {
  const notify = useNotify();
  const { data: groups = [], isPending: groupsPending, error: groupsError, refetch: refetchGroups } = useGetList<StudyGroup>("study_groups");
  const { data: chats = [], isPending: chatsPending, error: chatsError, refetch: refetchChats } = useGetList<VkChat>("vk_chats");
  const [createGroup, { isPending: isCreating }] = useCreate();
  const [updateChat] = useUpdate();
  const [dialogOpen, setDialogOpen] = useState(false);

  function submitGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const name = String(new FormData(form).get("name") ?? "");
    createGroup("study_groups", { data: { name } }, {
      onSuccess: () => {
        form.reset();
        setDialogOpen(false);
        notify("Учебная группа создана", { type: "success" });
      },
      onError: () => notify("Не удалось создать группу", { type: "error" }),
    });
  }

  function linkChat(chat: VkChat, studyGroupId: number | null) {
    updateChat("vk_chats", { id: chat.id, data: { study_group_id: studyGroupId }, previousData: chat }, {
      mutationMode: "optimistic",
      onSuccess: () => notify("Привязка сохранена", { type: "success" }),
      onError: () => notify("Не удалось сохранить привязку", { type: "error" }),
    });
  }

  return (
    <Stack spacing={3}>
      <Title title="Учебные группы" />
      <PageHeader title="Учебные группы" description="Подключение VK-бесед и классификация участников." />
      {groupsError || chatsError ? <QueryErrorState message="Не удалось загрузить группы и VK-беседы." onRetry={() => Promise.all([refetchGroups(), refetchChats()])} /> : null}
      <SectionCard title="Группы" action={<Button onClick={() => setDialogOpen(true)} startIcon={<AddIcon />} variant="outlined">Создать</Button>}>
        {groupsPending ? <LinearProgress /> : null}
        {!groupsPending && groups.length === 0 ? <EmptyState title="Групп пока нет" description="Создайте учебную группу и привяжите к ней VK-беседу." /> : (
          <TableContainer>
            <Table aria-label="Учебные группы">
              <TableHead><TableRow><TableCell>Название</TableCell><TableCell>VK-беседа</TableCell><TableCell>Состояние</TableCell><TableCell align="right">Действия</TableCell></TableRow></TableHead>
              <TableBody>
                {groups.map((group) => {
                  const chat = chats.find((item) => item.study_group_id === group.id);
                  return (
                    <TableRow hover key={group.id}>
                      <TableCell sx={{ fontWeight: 600 }}>{group.name}</TableCell>
                      <TableCell>{chat?.title ?? (chat ? `Беседа ${chat.id}` : "Не подключена")}</TableCell>
                      <TableCell><Chip color={chat ? "success" : "default"} label={chat ? "Подключена" : "Требует настройки"} size="small" variant={chat ? "filled" : "outlined"} /></TableCell>
                      <TableCell align="right">
                        {chat ? <Button component={Link} size="small" startIcon={<PeopleOutlineIcon />} to={`/study_groups/${group.id}/show`}>Участники</Button> : "—"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </SectionCard>

      <SectionCard title="Обнаруженные VK-беседы" description="Каждая беседа может быть связана только с одной группой.">
        {chatsPending ? <LinearProgress /> : null}
        {!chatsPending && chats.length === 0 ? <EmptyState title="Беседы пока не обнаружены" description="Добавьте бота в беседу и отправьте в ней сообщение." /> : (
          <TableContainer>
            <Table aria-label="VK-беседы">
              <TableHead><TableRow><TableCell>Название</TableCell><TableCell>Peer ID</TableCell><TableCell>Учебная группа</TableCell></TableRow></TableHead>
              <TableBody>
                {chats.map((chat) => (
                  <TableRow hover key={chat.id}>
                    <TableCell sx={{ fontWeight: 600 }}>{chat.title ?? `Беседа ${chat.id}`}</TableCell>
                    <TableCell>{chat.peer_id}</TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 220 }}>
                        <Select aria-label={`Учебная группа для ${chat.title ?? `беседы ${chat.id}`}`} onChange={(event) => linkChat(chat, Number(event.target.value) || null)} value={chat.study_group_id ?? ""}>
                          <MenuItem value="">Не назначена</MenuItem>
                          {groups.map((group) => <MenuItem key={group.id} value={group.id}>{group.name}</MenuItem>)}
                        </Select>
                      </FormControl>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </SectionCard>

      <Dialog fullWidth maxWidth="xs" onClose={() => setDialogOpen(false)} open={dialogOpen}>
        <form onSubmit={submitGroup}>
          <DialogTitle>Новая учебная группа</DialogTitle>
          <DialogContent><TextField autoFocus fullWidth label="Название группы" margin="dense" name="name" slotProps={{ htmlInput: { maxLength: 64 } }} required /></DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
            <Button disabled={isCreating} startIcon={isCreating ? <CircularProgress color="inherit" size={18} /> : <AddIcon />} type="submit" variant="contained">Создать</Button>
          </DialogActions>
        </form>
      </Dialog>
    </Stack>
  );
}
