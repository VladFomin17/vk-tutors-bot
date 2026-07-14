import { Admin } from "react-admin";

import { Dashboard } from "../features/dashboard/Dashboard";
import { authProvider } from "../services/authProvider";

export function App() {
  return <Admin authProvider={authProvider} dashboard={Dashboard} disableTelemetry />;
}
