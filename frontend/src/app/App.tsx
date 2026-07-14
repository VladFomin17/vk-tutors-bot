import { Admin } from "react-admin";

import { Dashboard } from "../features/dashboard/Dashboard";
import { authProvider } from "../services/authProvider";
import { dataProvider } from "../services/dataProvider";

export function App() {
  return (
    <Admin
      authProvider={authProvider}
      dashboard={Dashboard}
      dataProvider={dataProvider}
      disableTelemetry
    />
  );
}
