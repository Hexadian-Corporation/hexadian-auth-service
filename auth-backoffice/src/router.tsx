import { createBrowserRouter, Navigate } from "react-router";
import DashboardLayout from "@/layouts/DashboardLayout";
import LoginPage from "@/pages/LoginPage";
import UsersPage from "@/pages/UsersPage";
import UserDetailPage from "@/pages/UserDetailPage";
import PermissionsPage from "@/pages/PermissionsPage";
import RolesPage from "@/pages/RolesPage";
import RoleDetailPage from "@/pages/RoleDetailPage";
import GroupsPage from "@/pages/GroupsPage";
import GroupDetailPage from "@/pages/GroupDetailPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <DashboardLayout />,
    children: [
      { index: true, element: <Navigate to="/users" replace /> },
      { path: "users", element: <UsersPage /> },
      { path: "users/:id", element: <UserDetailPage /> },
      { path: "rbac/permissions", element: <PermissionsPage /> },
      { path: "rbac/roles", element: <RolesPage /> },
      { path: "rbac/roles/:id", element: <RoleDetailPage /> },
      { path: "rbac/groups", element: <GroupsPage /> },
      { path: "rbac/groups/:id", element: <GroupDetailPage /> },
    ],
  },
  {
    path: "/callback",
    element: <div>OAuth Callback — processing...</div>,
  },
]);
