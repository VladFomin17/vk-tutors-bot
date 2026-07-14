import { Box, Button, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type PageHeaderProps = {
  title: string;
  description?: string;
  action?: { label: string; to: string; icon?: ReactNode };
};

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <Box component="header">
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      sx={{ justifyContent: "space-between" }}
    >
      <Box>
        <Typography component="h1" variant="h4">
          {title}
        </Typography>
        {description ? (
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {description}
          </Typography>
        ) : null}
      </Box>
      {action ? (
        <Button component={Link} to={action.to} variant="contained" startIcon={action.icon}>
          {action.label}
        </Button>
      ) : null}
    </Stack>
    </Box>
  );
}
