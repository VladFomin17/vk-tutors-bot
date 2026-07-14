import SearchIcon from "@mui/icons-material/Search";
import {
  Chip,
  FormControl,
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
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { Title, useGetList } from "react-admin";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import type { Student } from "../../types/entities";
import { formatDateTime } from "../../utils/date";

type ActivityFilter = "all" | "active" | "inactive";

export function StudentListPage() {
  const { data = [], isPending, error, refetch } = useGetList<Student>("students");
  const [search, setSearch] = useState("");
  const [groupId, setGroupId] = useState("all");
  const [activity, setActivity] = useState<ActivityFilter>("active");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const groups = useMemo(
    () => [...new Map(data.map((student) => [student.study_group_id, student.study_group_name])).entries()].sort((left, right) => left[1].localeCompare(right[1], "ru-RU")),
    [data],
  );
  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("ru-RU");
    return data.filter((student) => {
      const identity = `${student.last_name} ${student.first_name} ${student.vk_user_id}`.toLocaleLowerCase("ru-RU");
      const matchesActivity = activity === "all" || (activity === "active") === student.is_active;
      return identity.includes(query) && matchesActivity && (groupId === "all" || student.study_group_id === Number(groupId));
    });
  }, [activity, data, groupId, search]);
  const visible = filtered.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  function resetPage() {
    setPage(0);
  }

  return (
    <Stack spacing={3}>
      <Title title="Студенты" />
      <PageHeader title="Студенты" description="Первокурсники, классифицированные в подключённых VK-беседах." />
      {error ? <QueryErrorState message="Не удалось загрузить студентов." onRetry={refetch} /> : null}
      <Paper variant="outlined">
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ p: 2 }}>
          <TextField
            aria-label="Поиск студентов"
            onChange={(event) => { setSearch(event.target.value); resetPage(); }}
            placeholder="Фамилия, имя или VK ID"
            size="small"
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> } }}
            sx={{ flex: 1, maxWidth: 440 }}
            value={search}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <Select aria-label="Фильтр по группе" onChange={(event) => { setGroupId(event.target.value); resetPage(); }} value={groupId}>
              <MenuItem value="all">Все группы</MenuItem>
              {groups.map(([id, name]) => <MenuItem key={id} value={String(id)}>{name}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 170 }}>
            <Select aria-label="Фильтр по активности" onChange={(event) => { setActivity(event.target.value as ActivityFilter); resetPage(); }} value={activity}>
              <MenuItem value="active">В беседе</MenuItem>
              <MenuItem value="inactive">Вышли из беседы</MenuItem>
              <MenuItem value="all">Все</MenuItem>
            </Select>
          </FormControl>
        </Stack>
        {isPending ? <LinearProgress /> : null}
        {!isPending && filtered.length === 0 ? (
          <EmptyState title={data.length === 0 ? "Студентов пока нет" : "Ничего не найдено"} description={data.length === 0 ? "Назначьте участникам подключённых бесед роль «Первокурсник»." : "Измените поиск или фильтры."} />
        ) : (
          <>
            <TableContainer>
              <Table aria-label="Список студентов">
                <TableHead><TableRow><TableCell>Студент</TableCell><TableCell>Группа</TableCell><TableCell>VK ID</TableCell><TableCell>Состояние</TableCell><TableCell>Последняя синхронизация</TableCell></TableRow></TableHead>
                <TableBody>{visible.map((student) => (
                  <TableRow hover key={student.id}>
                    <TableCell><Typography sx={{ fontWeight: 600 }}>{student.last_name} {student.first_name}</Typography></TableCell>
                    <TableCell>{student.study_group_name}</TableCell>
                    <TableCell>{student.vk_user_id}</TableCell>
                    <TableCell><Chip color={student.is_active ? "success" : "default"} label={student.is_active ? "В беседе" : "Вышел"} size="small" variant={student.is_active ? "filled" : "outlined"} /></TableCell>
                    <TableCell>{formatDateTime(student.last_seen_at)}</TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>
            </TableContainer>
            <TablePagination component="div" count={filtered.length} labelRowsPerPage="Строк на странице" onPageChange={(_, value) => setPage(value)} onRowsPerPageChange={(event) => { setRowsPerPage(Number(event.target.value)); resetPage(); }} page={page} rowsPerPage={rowsPerPage} rowsPerPageOptions={[10, 25, 50]} />
          </>
        )}
      </Paper>
    </Stack>
  );
}
