import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router";
import { Users, Shield, KeyRound, Layers, LogOut, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { clearTokens, redirectToPortal, hasAnyPermission } from "@/lib/auth";
import { changePassword } from "@/api/auth";
import ChangePasswordDialog from "@/components/ChangePasswordDialog";

const navItems = [
  { to: "/users", label: "Users", icon: Users, permissions: ["auth:users:read", "auth:users:admin"] },
  { to: "/rbac/permissions", label: "Permissions", icon: KeyRound, permissions: ["auth:rbac:manage"] },
  { to: "/rbac/roles", label: "Roles", icon: Shield, permissions: ["auth:rbac:manage"] },
  { to: "/rbac/groups", label: "Groups", icon: Layers, permissions: ["auth:rbac:manage"] },
];

const PORTAL_URL = import.meta.env.VITE_AUTH_PORTAL_URL ?? "http://localhost:3003";

export default function DashboardLayout() {
  const location = useLocation();
  const [showChangePassword, setShowChangePassword] = useState(false);

  async function handleChangePassword(oldPassword: string, newPassword: string) {
    await changePassword(oldPassword, newPassword);
    clearTokens();
    setTimeout(() => {
      window.location.href = `${PORTAL_URL}/login`;
    }, 2000);
  }

  return (
    <div className="flex h-screen bg-[#0f0f0f]">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-white/[0.04] bg-[#161616]">
        <div className="border-b border-white/[0.04] p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl bg-[#1a1a1a] shadow-[0_8px_24px_rgba(0,0,0,0.6)]">
              <img
                src="/brand/HEXADIAN-Background_Round.png"
                alt="Hexadian"
                className="h-9 w-9 rounded-lg"
              />
            </div>
            <div>
              <p className="text-sm font-semibold text-[#e6eef6]">Hexadian</p>
              <p className="text-xs text-[#888888]">Auth Backoffice</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {navItems
            .filter(({ permissions }) => hasAnyPermission(permissions))
            .map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                location.pathname.startsWith(to)
                  ? "bg-[#242424] text-[#e6eef6]"
                  : "text-[#888888] hover:bg-[#242424] hover:text-[#e6eef6]",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="border-t border-white/[0.04] p-2">
          <button
            onClick={() => setShowChangePassword(true)}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-[#888888] transition-colors hover:bg-[#242424] hover:text-[#e6eef6]"
          >
            <Lock className="h-4 w-4" />
            Change Password
          </button>
          <button
            onClick={() => { clearTokens(); redirectToPortal(); }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-[#888888] transition-colors hover:bg-[#242424] hover:text-[#e6eef6]"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>

      <ChangePasswordDialog
        open={showChangePassword}
        onClose={() => setShowChangePassword(false)}
        onSubmit={handleChangePassword}
      />
    </div>
  );
}
