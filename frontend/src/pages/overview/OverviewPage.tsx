import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import EventOutlinedIcon from "@mui/icons-material/EventOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import HowToRegOutlinedIcon from "@mui/icons-material/HowToRegOutlined";
import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import {
  Alert,
  Button,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { Title, useGetList, useGetOne } from "react-admin";
import { Link } from "react-router-dom";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { SectionCard } from "../../components/SectionCard";
import { StatCard } from "../../components/StatCard";
import { BroadcastStatusChip } from "../../components/StatusChip";
import type { Broadcast, Statistics, VkChat } from "../../types/entities";
import { formatDateTime } from "../../utils/date";

export function OverviewPage() {
  const { data: chats = [] } = useGetList<VkChat>("vk_chats");
  const { data: broadcasts = [], isPending: broadcastsPending } = useGetList<Broadcast>("broadcasts");
  const { data: statistics, isPending: statisticsPending } = useGetOne<Statistics>("statistics", { id: "current" });
  const now = Date.now();
  const active = broadcasts.filter((broadcast) => new Date(broadcast.deadline).getTime() >= now);
  const recent = [...broadcasts].sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()).slice(0, 5);
  const upcoming = [...active].sort((left, right) => new Date(left.deadline).getTime() - new Date(right.deadline).getTime()).slice(0, 5);
  const unlinkedChats = chats.filter((chat) => chat.study_group_id === null);

  return (
    <Stack spacing={3}>
      <Title title="Обзор" />
      <PageHeader title="Обзор" description="Состояние рассылок и подключённых учебных групп." action={{ label: "Создать рассылку", to: "/broadcasts/create" }} />
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<GroupsOutlinedIcon />} label="Учебные группы" loading={statisticsPending} value={statistics?.overview.total_groups ?? 0} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<PeopleOutlinedIcon />} label="Студенты" loading={statisticsPending} value={statistics?.overview.total_students ?? 0} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<CampaignOutlinedIcon />} label="Активные рассылки" loading={statisticsPending} value={statistics?.overview.active_broadcasts ?? 0} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<EventOutlinedIcon />} label="Завершённые" loading={statisticsPending} value={statistics?.overview.completed_broadcasts ?? 0} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<HowToRegOutlinedIcon />} label="Ответы сегодня" loading={statisticsPending} value={statistics?.overview.responses_today ?? 0} /></Grid>
      </Grid>

      {unlinkedChats.length > 0 ? <Alert severity="warning">{unlinkedChats.length} {unlinkedChats.length === 1 ? "беседа не привязана" : "беседы не привязаны"} к учебной группе. <Button component={Link} size="small" to="/study_groups">Настроить</Button></Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <SectionCard title="Последние рассылки" action={<Button component={Link} to="/broadcasts">Все рассылки</Button>}>
            {broadcastsPending ? <LinearProgress /> : null}
            {!broadcastsPending && recent.length === 0 ? <EmptyState title="Рассылок пока нет" description="Создайте первую рассылку для учебных групп." /> : (
              <TableContainer>
                <Table aria-label="Последние рассылки">
                  <TableHead><TableRow><TableCell>Название</TableCell><TableCell>Статус</TableCell><TableCell>Дедлайн</TableCell><TableCell align="right">Получатели</TableCell></TableRow></TableHead>
                  <TableBody>{recent.map((broadcast) => <TableRow hover key={broadcast.id}><TableCell><Link style={{ color: "inherit", fontWeight: 600, textDecoration: "none" }} to={`/broadcasts/${broadcast.id}/show`}>{broadcast.title}</Link></TableCell><TableCell><BroadcastStatusChip deadline={broadcast.deadline} /></TableCell><TableCell>{formatDateTime(broadcast.deadline)}</TableCell><TableCell align="right">{broadcast.recipient_count}</TableCell></TableRow>)}</TableBody>
                </Table>
              </TableContainer>
            )}
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <SectionCard title="Ближайшие дедлайны">
            {broadcastsPending ? <LinearProgress /> : null}
            {!broadcastsPending && upcoming.length === 0 ? <EmptyState title="Нет ближайших дедлайнов" /> : (
              <List disablePadding>{upcoming.map((broadcast, index) => <ListItem divider={index < upcoming.length - 1} key={broadcast.id} disableGutters><ListItemText primary={<Link style={{ color: "inherit", fontWeight: 600, textDecoration: "none" }} to={`/broadcasts/${broadcast.id}/show`}>{broadcast.title}</Link>} secondary={formatDateTime(broadcast.deadline)} /></ListItem>)}</List>
            )}
          </SectionCard>
        </Grid>
      </Grid>
    </Stack>
  );
}
