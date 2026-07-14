import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import HowToRegOutlinedIcon from "@mui/icons-material/HowToRegOutlined";
import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import TaskAltOutlinedIcon from "@mui/icons-material/TaskAltOutlined";
import { Grid, LinearProgress, Stack, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import { LineChart } from "@mui/x-charts/LineChart";
import { Title, useGetOne } from "react-admin";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { SectionCard } from "../../components/SectionCard";
import { StatCard } from "../../components/StatCard";
import type { Statistics } from "../../types/entities";

export function StatisticsPage() {
  const { data, isPending, error, refetch } = useGetOne<Statistics>("statistics", { id: "current" });
  if (error) return <QueryErrorState message="Не удалось загрузить статистику." onRetry={refetch} />;
  if (isPending || !data) return <LinearProgress />;
  const groupPercentages = data.group_activity.map((group) => group.recipient_count === 0 ? 0 : Math.round(group.response_count / group.recipient_count * 100));

  return (
    <Stack spacing={3}>
      <Title title="Статистика" />
      <PageHeader title="Статистика" description="Ответы и выполнение рассылок по актуальным данным системы." />
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<GroupsOutlinedIcon />} label="Группы" value={data.overview.total_groups} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<PeopleOutlinedIcon />} label="Студенты" value={data.overview.total_students} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<CampaignOutlinedIcon />} label="Активные" value={data.overview.active_broadcasts} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<TaskAltOutlinedIcon />} label="Завершённые" value={data.overview.completed_broadcasts} /></Grid>
        <Grid size={{ xs: 12, sm: 6, xl: 2.4 }}><StatCard icon={<HowToRegOutlinedIcon />} label="Ответы сегодня" value={data.overview.responses_today} /></Grid>
      </Grid>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <SectionCard title="Ответы за 14 дней">
            <LineChart
              height={300}
              series={[{ data: data.responses_over_time.map((item) => item.count), label: "Ответы", showMark: true }]}
              xAxis={[{ data: data.responses_over_time.map((item) => new Date(`${item.date}T00:00:00`).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" })), scaleType: "point" }]}
              yAxis={[{ min: 0 }]}
            />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 5 }}>
          <SectionCard title="Выполнение по группам" description="По всем сохранённым снимкам рассылок.">
            {data.group_activity.length === 0 ? <EmptyState title="Данных пока нет" /> : (
              <BarChart
                height={300}
                series={[{ data: groupPercentages, label: "Выполнение, %" }]}
                xAxis={[{ data: data.group_activity.map((group) => group.name), scaleType: "band" }]}
                yAxis={[{ max: 100, min: 0 }]}
              />
            )}
          </SectionCard>
        </Grid>
      </Grid>
      <SectionCard title="Последние рассылки" description="Доля ответивших в снимке каждой рассылки.">
        {data.broadcast_completion.length === 0 ? <EmptyState title="Рассылок пока нет" /> : (
          <Stack spacing={2}>{data.broadcast_completion.map((broadcast) => {
            const percent = broadcast.recipient_count === 0 ? 0 : Math.round(broadcast.response_count / broadcast.recipient_count * 100);
            return <Stack key={broadcast.id} spacing={0.75}>
              <Stack direction="row" sx={{ justifyContent: "space-between" }}><Typography sx={{ fontWeight: 600 }}>{broadcast.title}</Typography><Typography color="text.secondary">{broadcast.response_count} из {broadcast.recipient_count} · {percent}%</Typography></Stack>
              <LinearProgress aria-label={`Выполнение рассылки ${broadcast.title}`} sx={{ height: 7, borderRadius: 4 }} value={percent} variant="determinate" />
            </Stack>;
          })}</Stack>
        )}
      </SectionCard>
    </Stack>
  );
}
