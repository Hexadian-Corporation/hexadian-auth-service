import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router";
import { Users, Shield, KeyRound, Layers, LogOut, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { clearTokens, redirectToPortal } from "@/lib/auth";
import { changePassword } from "@/api/auth";
import ChangePasswordDialog from "@/components/ChangePasswordDialog";

const navItems = [
  { to: "/users", label: "Users", icon: Users },
  { to: "/rbac/permissions", label: "Permissions", icon: KeyRound },
  { to: "/rbac/roles", label: "Roles", icon: Shield },
  { to: "/rbac/groups", label: "Groups", icon: Layers },
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
    <div className="flex h-screen bg-[#0b0e17]">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-slate-700 bg-slate-900">
        <div className="border-b border-slate-700 p-4">
          <img
            src="/brand/HEXADIAN-Letters.svg"
            alt="Hexadian"
            className="h-7"
          />
          <p className="mt-1 text-xs text-slate-400">Auth Backoffice</p>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                location.pathname.startsWith(to)
                  ? "bg-slate-800 text-cyan-400"
                  : "text-slate-300 hover:bg-slate-800 hover:text-slate-100",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="border-t border-slate-700 p-2">
          <button
            onClick={() => setShowChangePassword(true)}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-slate-100"
          >
            <Lock className="h-4 w-4" />
            Change Password
          </button>
          <button
            onClick={() => { clearTokens(); redirectToPortal(); }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-slate-100"
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
