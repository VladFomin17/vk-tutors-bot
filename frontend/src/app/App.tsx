import { LinearProgress } from "@mui/material";
import { lazy, Suspense, type ComponentType, type LazyExoticComponent } from "react";
import { Admin, Resource } from "react-admin";

import { AdminLayout, broadcastIcon, groupIcon } from "../layouts/AdminLayout";
import { authProvider } from "../services/authProvider";
import { dataProvider } from "../services/dataProvider";
import { theme } from "./theme";

const OverviewPage = withSuspense(lazy(() => import("../pages/overview/OverviewPage").then((module) => ({ default: module.OverviewPage }))));
const BroadcastListPage = withSuspense(lazy(() => import("../pages/broadcasts/BroadcastListPage").then((module) => ({ default: module.BroadcastListPage }))));
const BroadcastCreatePage = withSuspense(lazy(() => import("../pages/broadcasts/BroadcastCreatePage").then((module) => ({ default: module.BroadcastCreatePage }))));
const BroadcastShowPage = withSuspense(lazy(() => import("../pages/broadcasts/BroadcastShowPage").then((module) => ({ default: module.BroadcastShowPage }))));
const GroupListPage = withSuspense(lazy(() => import("../pages/groups/GroupListPage").then((module) => ({ default: module.GroupListPage }))));
const GroupShowPage = withSuspense(lazy(() => import("../pages/groups/GroupShowPage").then((module) => ({ default: module.GroupShowPage }))));

export function App() {
  return (
    <Admin
      authProvider={authProvider}
      dashboard={OverviewPage}
      dataProvider={dataProvider}
      disableTelemetry
      layout={AdminLayout}
      theme={theme}
    >
      <Resource create={BroadcastCreatePage} icon={broadcastIcon} list={BroadcastListPage} name="broadcasts" options={{ label: "Рассылки" }} show={BroadcastShowPage} />
      <Resource icon={groupIcon} list={GroupListPage} name="study_groups" options={{ label: "Учебные группы" }} show={GroupShowPage} />
      <Resource name="vk_chats" />
      <Resource name="chat_members" />
      <Resource name="broadcast_results" />
    </Admin>
  );
}

function withSuspense(Component: LazyExoticComponent<ComponentType>) {
  return function SuspendedPage() {
    return <Suspense fallback={<LinearProgress />}><Component /></Suspense>;
  };
}
