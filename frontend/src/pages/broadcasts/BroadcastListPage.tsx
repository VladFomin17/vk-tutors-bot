import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  IconButton,
  InputAdornment,
  LinearProgress,
  Menu,
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
  Tooltip,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useMemo, useState, type MouseEvent } from "react";
import { Title, useDelete, useGetList, useNotify } from "react-admin";
import { Link } from "react-router-dom";

import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { QueryErrorState } from "../../components/QueryErrorState";
import { BroadcastStatusChip } from "../../components/StatusChip";
import type { Broadcast } from "../../types/entities";
import { isBroadcastCompleted, sortBroadcasts, type BroadcastSort } from "../../utils/broadcasts";
import { formatDateTime } from "../../utils/date";

type StatusFilter = "all" | "active" | "completed";

export function BroadcastListPage() {
  const notify = useNotify();
  const { data = [], isPending, error, refetch } = useGetList<Broadcast>("broadcasts");
  const [deleteBroadcast, { isPending: isDeleting }] = useDelete();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [sort, setSort] = useState<BroadcastSort>("created_desc");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [broadcastToDelete, setBroadcastToDelete] = useState<Broadcast | null>(null);

  const filtered = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("ru-RU");
    const rows = data.filter((broadcast) => {
      const completed = isBroadcastCompleted(broadcast.deadline);
      const matchesStatus = status === "all" || (status === "completed") === completed;
      return matchesStatus && broadcast.title.toLocaleLowerCase("ru-RU").includes(query);
    });
    return sortBroadcasts(rows, sort);
  }, [data, search, sort, status]);

  const visibleRows = filtered.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  function confirmDelete() {
    if (broadcastToDelete === null) return;
    deleteBroadcast(
      "broadcasts",
      { id: broadcastToDelete.id, previousData: broadcastToDelete },
      {
        onSuccess: () => {
          setBroadcastToDelete(null);
          notify("Рассылка и связанные данные удалены", { type: "success" });
        },
        onError: (error) => notify(error instanceof Error ? error.message : "Не удалось удалить рассылку", { type: "error" }),
      },
    );
  }

  return (
    <Stack spacing={3}>
      <Title title="Рассылки" />
      <PageHeader
        title="Рассылки"
        description="Создание, контроль ответов и экспорт результатов."
      />
      {error ? <QueryErrorState message="Не удалось загрузить рассылки." onRetry={refetch} /> : null}
      <Paper variant="outlined">
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ p: 2 }}>
          <TextField
            aria-label="Поиск рассылок"
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(0);
            }}
            placeholder="Поиск по названию"
            size="small"
            value={search}
            sx={{ flex: 1, maxWidth: 420 }}
            slotProps={{
              input: { startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> },
            }}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <Select
              aria-label="Статус рассылки"
              onChange={(event) => {
                setStatus(event.target.value as StatusFilter);
                setPage(0);
              }}
              value={status}
            >
              <MenuItem value="all">Все статусы</MenuItem>
              <MenuItem value="active">Активные</MenuItem>
              <MenuItem value="completed">Завершённые</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 190 }}>
            <Select aria-label="Сортировка рассылок" onChange={(event) => setSort(event.target.value as BroadcastSort)} value={sort}>
              <MenuItem value="created_desc">Сначала новые</MenuItem>
              <MenuItem value="deadline_asc">Ближайший дедлайн</MenuItem>
              <MenuItem value="deadline_desc">Поздний дедлайн</MenuItem>
              <MenuItem value="title_asc">По названию</MenuItem>
            </Select>
          </FormControl>
        </Stack>
        {isPending ? <LinearProgress /> : null}
        {!isPending && filtered.length === 0 ? (
          <EmptyState
            title={data.length === 0 ? "Рассылок пока нет" : "Ничего не найдено"}
            description={data.length === 0 ? "Создайте первую рассылку для учебных групп." : "Измените поиск или фильтр."}
          />
        ) : (
          <>
            <TableContainer>
              <Table aria-label="Список рассылок">
                <TableHead>
                  <TableRow>
                    <TableCell>Название</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Дедлайн</TableCell>
                    <TableCell align="right">Группы</TableCell>
                    <TableCell align="right">Получатели</TableCell>
                    <TableCell align="right">Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {visibleRows.map((broadcast) => (
                    <TableRow hover key={broadcast.id}>
                      <TableCell>
                        <Box component={Link} to={`/broadcasts/${broadcast.id}/show`} sx={{ color: "text.primary", fontWeight: 600, textDecoration: "none" }}>
                          {broadcast.title}
                        </Box>
                      </TableCell>
                      <TableCell><BroadcastStatusChip deadline={broadcast.deadline} /></TableCell>
                      <TableCell>{formatDateTime(broadcast.deadline)}</TableCell>
                      <TableCell align="right">{broadcast.target_count}</TableCell>
                      <TableCell align="right">{broadcast.recipient_count}</TableCell>
                      <TableCell align="right"><BroadcastActions broadcast={broadcast} onDelete={setBroadcastToDelete} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={filtered.length}
              labelRowsPerPage="Строк на странице"
              onPageChange={(_, nextPage) => setPage(nextPage)}
              onRowsPerPageChange={(event) => {
                setRowsPerPage(Number(event.target.value));
                setPage(0);
              }}
              page={page}
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[10, 25, 50]}
            />
          </>
        )}
      </Paper>
      <Dialog onClose={() => !isDeleting && setBroadcastToDelete(null)} open={broadcastToDelete !== null}>
        <DialogTitle>Удалить рассылку?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            «{broadcastToDelete?.title}» будет удалена вместе с результатами, заданиями и сохранёнными изображениями. Уже отправленные сообщения останутся в VK.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button disabled={isDeleting} onClick={() => setBroadcastToDelete(null)}>Отмена</Button>
          <Button color="error" disabled={isDeleting} onClick={confirmDelete} startIcon={isDeleting ? <CircularProgress color="inherit" size={18} /> : <DeleteOutlineIcon />}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

function BroadcastActions({ broadcast, onDelete }: { broadcast: Broadcast; onDelete: (broadcast: Broadcast) => void }) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const close = () => setAnchor(null);
  const open = (event: MouseEvent<HTMLElement>) => setAnchor(event.currentTarget);
  return (
    <>
      <Tooltip title="Действия">
        <IconButton aria-label="Действия с рассылкой" onClick={open} size="small"><MoreHorizIcon /></IconButton>
      </Tooltip>
      <Menu anchorEl={anchor} onClose={close} open={Boolean(anchor)}>
        <MenuItem component={Link} onClick={close} to={`/broadcasts/${broadcast.id}/show`}>
          <VisibilityOutlinedIcon fontSize="small" sx={{ mr: 1.5 }} /> Результаты
        </MenuItem>
        <MenuItem component="a" href={`/api/v1/broadcasts/${broadcast.id}/export.xlsx`} onClick={close}>
          <DownloadOutlinedIcon fontSize="small" sx={{ mr: 1.5 }} /> Скачать XLSX
        </MenuItem>
        <MenuItem component="a" href={`/api/v1/broadcasts/${broadcast.id}/export.docx`} onClick={close}>
          <DownloadOutlinedIcon fontSize="small" sx={{ mr: 1.5 }} /> Скачать DOCX
        </MenuItem>
        <MenuItem onClick={() => { close(); onDelete(broadcast); }} sx={{ color: "error.main" }}>
          <DeleteOutlineIcon fontSize="small" sx={{ mr: 1.5 }} /> Удалить
        </MenuItem>
      </Menu>
    </>
  );
}
