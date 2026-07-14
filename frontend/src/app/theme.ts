import type { RaThemeOptions } from "react-admin";

export const theme: RaThemeOptions = {
  palette: {
    mode: "light",
    primary: { main: "#4f46e5" },
    background: { default: "#f7f7f8", paper: "#ffffff" },
    text: { primary: "#18181b", secondary: "#71717a" },
    divider: "#e4e4e7",
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
    h4: { fontSize: "1.75rem", fontWeight: 700, letterSpacing: "-0.025em" },
    h6: { fontWeight: 650, letterSpacing: "-0.01em" },
    button: { fontWeight: 600, textTransform: "none" },
  },
  components: {
    MuiCard: { styleOverrides: { root: { boxShadow: "none" } } },
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiTableCell: { styleOverrides: { head: { fontWeight: 650, color: "#52525b" } } },
  },
};
