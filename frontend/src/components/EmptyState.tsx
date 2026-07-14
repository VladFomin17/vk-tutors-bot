import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import { Box, Typography } from "@mui/material";

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <Box sx={{ py: 6, px: 2, textAlign: "center", color: "text.secondary" }}>
      <InboxOutlinedIcon sx={{ fontSize: 36, mb: 1, color: "action.disabled" }} />
      <Typography color="text.primary" sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      {description ? <Typography variant="body2">{description}</Typography> : null}
    </Box>
  );
}
