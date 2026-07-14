import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutlined";
import CampaignOutlinedIcon from "@mui/icons-material/CampaignOutlined";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import { Box, Button } from "@mui/material";
import {
  AppBar,
  Layout,
  type LayoutProps,
  Menu,
  TitlePortal,
  UserMenu,
} from "react-admin";
import { Link } from "react-router-dom";

function AdminAppBar() {
  return (
    <AppBar color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
      <TitlePortal />
      <Box sx={{ flex: 1 }} />
      <Button
        component={Link}
        to="/broadcasts/create"
        startIcon={<AddCircleOutlineIcon />}
        sx={{ display: { xs: "none", sm: "inline-flex" }, mr: 1 }}
        variant="contained"
      >
        Создать рассылку
      </Button>
      <UserMenu />
    </AppBar>
  );
}

function AdminMenu() {
  return (
    <Menu sx={{ mt: 1 }}>
      <Menu.DashboardItem leftIcon={<DashboardOutlinedIcon />} primaryText="Обзор" />
      <Menu.ResourceItem name="broadcasts" />
      <Menu.Item
        leftIcon={<AddCircleOutlineIcon />}
        primaryText="Создать рассылку"
        to="/broadcasts/create"
      />
      <Menu.ResourceItem name="study_groups" />
    </Menu>
  );
}

export function AdminLayout(props: LayoutProps) {
  return <Layout {...props} appBar={AdminAppBar} menu={AdminMenu} />;
}

export const broadcastIcon = CampaignOutlinedIcon;
export const groupIcon = GroupsOutlinedIcon;
