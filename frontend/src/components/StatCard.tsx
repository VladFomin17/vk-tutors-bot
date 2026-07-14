import { Card, CardContent, Skeleton, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

export function StatCard({ label, value, icon, loading = false }: { label: string; value: number; icon: ReactNode; loading?: boolean }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <Typography color="text.secondary" variant="body2">{label}</Typography>
            {loading ? <Skeleton width={60} height={44} /> : <Typography sx={{ mt: 0.5 }} variant="h4">{value}</Typography>}
          </div>
          <Stack sx={{ alignItems: "center", bgcolor: "action.hover", borderRadius: 2, color: "text.secondary", height: 40, justifyContent: "center", width: 40 }}>{icon}</Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
