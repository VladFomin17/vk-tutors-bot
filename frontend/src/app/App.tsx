import { Admin, Resource } from "react-admin";

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
    >
      <Resource name="study_groups" />
      <Resource name="vk_chats" />
    </Admin>
  );
}
