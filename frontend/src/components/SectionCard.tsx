import { Card, CardContent, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

type SectionCardProps = {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function SectionCard({ title, description, action, children }: SectionCardProps) {
  return (
    <Card variant="outlined">
      <CardContent>
        {title || action ? (
          <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
            <div>
              {title ? <Typography variant="h6">{title}</Typography> : null}
              {description ? <Typography color="text.secondary">{description}</Typography> : null}
            </div>
            {action}
          </Stack>
        ) : null}
        {children}
      </CardContent>
    </Card>
  );
}
