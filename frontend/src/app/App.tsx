import { Admin } from "react-admin";

import { Dashboard } from "../features/dashboard/Dashboard";

export function App() {
  return <Admin dashboard={Dashboard} disableTelemetry />;
}
