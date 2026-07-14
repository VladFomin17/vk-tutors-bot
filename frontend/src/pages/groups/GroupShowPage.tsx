import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SearchIcon from "@mui/icons-material/Search";
import {
  Button,
  Chip,
  FormControl,
  InputAdornment,
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
import { useMemo, useState } from "react";
import { Title, useGetList, useNotify, useUpdate } from "react-admin";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { SectionCard } from "../../components/SectionCard";
import type { ChatMember, MemberRole, StudyGroup, VkChat } from "../../types/entities";

const roleLabels: Record<MemberRole, string> = {
  unknown: "Не классифицирован",
  student: "Первокурсник",
  tutor: "Тьютор",
  leader: "Руководитель",
};

export function GroupShowPage() {
  const { id } = useParams();
  const groupId = Number(id);
  const notify = useNotify();
  const [updateMember] = useUpdate();
  const [search, setSearch] = useState("");
  const { data: groups = [], error: groupsError, refetch: refetchGroups } = useGetList<StudyGroup>("study_groups");
  const { data: chats = [], error: chatsError, refetch: refetchChats } = useGetList<VkChat>("vk_chats");
  const group = groups.find((item) => item.id === groupId);
  const chat = chats.find((item) => item.study_group_id === groupId);
  const { data: members = [], isPending, error: membersError, refetch: refetchMembers } = useGetList<ChatMember>("chat_members", { filter: { chat_id: chat?.id } }, { enabled: chat !== undefined });

  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("ru-RU");
    return members.filter((member) => `${member.last_name ?? ""} ${member.first_name ?? ""}`.toLocaleLowerCase("ru-RU").includes(query));
  }, [members, search]);

  function updateRole(member: ChatMember, role: MemberRole) {
    updateMember("chat_members", { id: member.id, data: { ...member, role }, previousData: member }, {
      mutationMode: "optimistic",
      onSuccess: () => notify("Роль сохранена", { type: "success" }),
      onError: () => notify("Не удалось сохранить роль", { type: "error" }),
    });
  }

  return (
    <Stack spacing={3}>
      <Title title={group?.name ?? "Участники группы"} />
      <PageHeader title={group?.name ?? "Участники группы"} description={chat ? `VK-беседа: ${chat.title ?? `Беседа ${chat.id}`}` : "К группе не подключена VK-беседа."} />
      {groupsError || chatsError || membersError ? <QueryErrorState message="Не удалось загрузить группу и её участников." onRetry={() => Promise.all([refetchGroups(), refetchChats(), refetchMembers()])} /> : null}
      <Button component={Link} startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }} to="/study_groups">К группам</Button>
      <SectionCard title="Участники" description="Роль определяет, кто попадёт в снимок получателей рассылки.">
        <TextField aria-label="Поиск участников" onChange={(event) => setSearch(event.target.value)} placeholder="Поиск по имени" size="small" slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> } }} sx={{ mb: 2, maxWidth: 420 }} value={search} />
        {isPending ? <LinearProgress /> : null}
        {!isPending && filtered.length === 0 ? <EmptyState title={members.length === 0 ? "Участники не найдены" : "Ничего не найдено"} description={members.length === 0 ? "Отправьте сообщение в VK-беседе, чтобы обновить список участников." : "Измените поисковый запрос."} /> : (
          <TableContainer>
            <Table aria-label="Участники группы">
              <TableHead><TableRow><TableCell>Участник</TableCell><TableCell>VK ID</TableCell><TableCell>Состояние</TableCell><TableCell>Роль</TableCell></TableRow></TableHead>
              <TableBody>
                {filtered.map((member) => (
                  <TableRow hover key={member.id}>
                    <TableCell sx={{ fontWeight: 600 }}>{`${member.last_name ?? ""} ${member.first_name ?? ""}`.trim() || `VK ID ${member.vk_user_id}`}</TableCell>
                    <TableCell>{member.vk_user_id}</TableCell>
                    <TableCell><Chip color={member.is_active ? "success" : "default"} label={member.is_active ? "В беседе" : "Не в беседе"} size="small" variant="outlined" /></TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 200 }}>
                        <Select aria-label={`Роль участника ${member.vk_user_id}`} onChange={(event) => updateRole(member, event.target.value as MemberRole)} value={member.role}>
                          {Object.entries(roleLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
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
    </Stack>
  );
}
