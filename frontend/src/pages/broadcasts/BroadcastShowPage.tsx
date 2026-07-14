import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ImageOutlinedIcon from "@mui/icons-material/ImageOutlined";
import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputAdornment,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { Title, useGetList } from "react-admin";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { SectionCard } from "../../components/SectionCard";
import { BroadcastStatusChip } from "../../components/StatusChip";
import type { Broadcast, BroadcastResult } from "../../types/entities";
import { formatDateTime } from "../../utils/date";

type ResultFilter = "all" | "responded" | "unanswered";

export function BroadcastShowPage() {
  const { id } = useParams();
  const broadcastId = Number(id);
  const { data: broadcasts = [], error: broadcastsError, refetch: refetchBroadcasts } = useGetList<Broadcast>("broadcasts");
  const { data: results = [], isPending, error: resultsError, refetch: refetchResults } = useGetList<BroadcastResult>("broadcast_results", { filter: { broadcast_id: broadcastId } }, { enabled: Number.isFinite(broadcastId) });
  const broadcast = broadcasts.find((item) => item.id === broadcastId);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ResultFilter>("all");
  const [group, setGroup] = useState("all");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const respondedCount = results.filter((result) => result.responded).length;
  const completion = results.length === 0 ? 0 : Math.round((respondedCount / results.length) * 100);
  const groups = [...new Set(results.map((result) => result.study_group_name))].sort();

  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("ru-RU");
    return results.filter((result) => {
      const fullName = `${result.last_name ?? ""} ${result.first_name ?? ""}`.toLocaleLowerCase("ru-RU");
      const matchesStatus = status === "all" || (status === "responded") === result.responded;
      return matchesStatus && (group === "all" || result.study_group_name === group) && fullName.includes(query);
    });
  }, [group, results, search, status]);

  return (
    <Stack spacing={3}>
      <Title title={broadcast?.title ?? "Результаты рассылки"} />
      <PageHeader title={broadcast?.title ?? "Результаты рассылки"} description={broadcast ? `Дедлайн: ${formatDateTime(broadcast.deadline)}` : "Загрузка данных рассылки…"} />
      {broadcastsError || resultsError ? <QueryErrorState message="Не удалось загрузить результаты рассылки." onRetry={() => Promise.all([refetchBroadcasts(), refetchResults()])} /> : null}
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
        <Button component={Link} startIcon={<ArrowBackIcon />} to="/broadcasts">К рассылкам</Button>
        <Button component="a" href={`/api/v1/broadcasts/${broadcastId}/export.xlsx`} startIcon={<DownloadOutlinedIcon />} variant="outlined">XLSX</Button>
        <Button component="a" href={`/api/v1/broadcasts/${broadcastId}/export.docx`} startIcon={<DownloadOutlinedIcon />} variant="outlined">DOCX</Button>
      </Stack>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 4 }}><Metric label="Ответили" value={`${respondedCount} из ${results.length}`} /></Grid>
        <Grid size={{ xs: 12, sm: 4 }}><Metric label="Выполнение" value={`${completion}%`} progress={completion} /></Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <SectionCard title="Статус">
            {broadcast ? <BroadcastStatusChip deadline={broadcast.deadline} /> : <Chip label="Загрузка" size="small" />}
          </SectionCard>
        </Grid>
      </Grid>

      <SectionCard title="Ответы" description="Последующий корректный ответ заменяет предыдущий.">
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ mb: 2 }}>
          <TextField
            aria-label="Поиск студентов"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Поиск по студенту"
            size="small"
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> } }}
            sx={{ flex: 1 }}
            value={search}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <Select aria-label="Фильтр по ответу" onChange={(event) => setStatus(event.target.value as ResultFilter)} value={status}>
              <MenuItem value="all">Все ответы</MenuItem>
              <MenuItem value="responded">Ответили</MenuItem>
              <MenuItem value="unanswered">Не ответили</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <Select aria-label="Фильтр по группе" onChange={(event) => setGroup(event.target.value)} value={group}>
              <MenuItem value="all">Все группы</MenuItem>
              {groups.map((name) => <MenuItem key={name} value={name}>{name}</MenuItem>)}
            </Select>
          </FormControl>
        </Stack>
        {isPending ? <LinearProgress /> : null}
        {!isPending && filtered.length === 0 ? (
          <EmptyState title={results.length === 0 ? "В снимке рассылки нет студентов" : "Ничего не найдено"} description={results.length === 0 ? "Тестовая рассылка могла быть отправлена в беседу без классифицированных студентов." : "Измените поиск или фильтры."} />
        ) : (
          <TableContainer component={Paper} variant="outlined">
            <Table aria-label="Результаты рассылки">
              <TableHead><TableRow><TableCell>Группа</TableCell><TableCell>Студент</TableCell><TableCell>Статус</TableCell><TableCell>Ответ</TableCell><TableCell>Вложения</TableCell></TableRow></TableHead>
              <TableBody>
                {filtered.map((result) => (
                  <TableRow hover key={result.id}>
                    <TableCell>{result.study_group_name}</TableCell>
                    <TableCell>{`${result.last_name ?? ""} ${result.first_name ?? ""}`.trim() || `VK ID ${result.vk_user_id}`}</TableCell>
                    <TableCell>
                      <Chip color={result.responded ? (result.is_late ? "warning" : "success") : "default"} label={result.responded ? (result.is_late ? "После дедлайна" : "Ответил") : "Не ответил"} size="small" variant={result.responded ? "filled" : "outlined"} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{result.text || "—"}</Typography>
                      {result.responded_at ? <Typography color="text.secondary" variant="caption">{formatDateTime(result.responded_at)}</Typography> : null}
                    </TableCell>
                    <TableCell>
                      <ResultImages onOpen={setImageUrl} result={result} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </SectionCard>

      <Dialog fullWidth maxWidth="md" onClose={() => setImageUrl(null)} open={imageUrl !== null}>
        <DialogTitle>Изображение ответа</DialogTitle>
        <DialogContent>{imageUrl ? <Box alt="Изображение, прикреплённое к ответу" component="img" src={imageUrl} sx={{ display: "block", maxHeight: "75vh", maxWidth: "100%", mx: "auto" }} /> : null}</DialogContent>
      </Dialog>
    </Stack>
  );
}

function ResultImages({ result, onOpen }: { result: BroadcastResult; onOpen: (url: string) => void }) {
  const urls = resultImageUrls(result);
  if (urls.length === 0) return <>—</>;
  return <Stack direction="row" spacing={0.5}>{urls.map((url, index) => <Button key={url} onClick={() => onOpen(url)} size="small" startIcon={<ImageOutlinedIcon />}>Фото {index + 1}</Button>)}</Stack>;
}

function Metric({ label, value, progress }: { label: string; value: string; progress?: number }) {
  return (
    <SectionCard title={label}>
      <Typography variant="h4">{value}</Typography>
      {progress === undefined ? null : <LinearProgress aria-label={label} sx={{ mt: 1.5, height: 6, borderRadius: 3 }} value={progress} variant="determinate" />}
    </SectionCard>
  );
}

function resultImageUrls(result: BroadcastResult): string[] {
  if (result.media.length > 0) return result.media.map((media) => `/api/v1/response-media/${media.id}`);
  return result.attachments.flatMap((attachment) => {
    if (attachment.type !== "photo") return [];
    const sizes = attachment.photo?.sizes ?? [];
    const url = sizes[sizes.length - 1]?.url;
    return url ? [url] : [];
  });
}
