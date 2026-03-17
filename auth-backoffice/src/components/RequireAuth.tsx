import { Outlet, useLocation } from "react-router";
import { isAuthenticated, redirectToPortal, hasAnyPermission } from "@/lib/auth";
import ForbiddenPage from "@/pages/ForbiddenPage";

const REQUIRED_PERMISSIONS = [
  "auth:users:read",
  "auth:users:admin",
  "auth:rbac:manage",
];

export default function RequireAuth() {
  const location = useLocation();

  if (!isAuthenticated()) {
    redirectToPortal(location.pathname + location.search);
    return null;
  }

  if (!hasAnyPermission(REQUIRED_PERMISSIONS)) {
    return <ForbiddenPage />;
  }

  return <Outlet />;
}
