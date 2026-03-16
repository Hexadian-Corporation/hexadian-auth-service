import { Outlet, useLocation } from "react-router";
import { isAuthenticated, redirectToPortal } from "@/lib/auth";

export default function RequireAuth() {
  const location = useLocation();

  if (!isAuthenticated()) {
    redirectToPortal(location.pathname + location.search);
    return null;
  }

  return <Outlet />;
}
