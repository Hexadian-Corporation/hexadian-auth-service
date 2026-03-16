import { Link, Outlet, useLocation } from "react-router";
import { Users, Shield, KeyRound, Layers, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { clearTokens, redirectToPortal } from "@/lib/auth";

const navItems = [
  { to: "/users", label: "Users", icon: Users },
  { to: "/rbac/permissions", label: "Permissions", icon: KeyRound },
  { to: "/rbac/roles", label: "Roles", icon: Shield },
  { to: "/rbac/groups", label: "Groups", icon: Layers },
];

export default function DashboardLayout() {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r bg-white">
        <div className="border-b p-4">
          <h2 className="text-lg font-bold text-gray-900">Hexadian</h2>
          <p className="text-xs text-gray-500">Auth Backoffice</p>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                location.pathname.startsWith(to)
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="border-t p-2">
          <button
            onClick={() => { clearTokens(); redirectToPortal(); }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"
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
    </div>
  );
}
