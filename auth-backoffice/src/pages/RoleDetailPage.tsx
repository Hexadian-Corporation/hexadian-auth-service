import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { ArrowLeft, Check } from "lucide-react";
import type { Permission, RoleCreate } from "@/types/rbac";
import * as rbacApi from "@/api/rbac";

function groupPermissionsByService(permissions: Permission[]): Record<string, Permission[]> {
  const groups: Record<string, Permission[]> = {};
  for (const perm of permissions) {
    const parts = perm.code.split(":");
    const service = parts.length > 2 ? parts.slice(0, -1).join(":") : parts.length > 1 ? parts[0] : "other";
    if (!groups[service]) {
      groups[service] = [];
    }
    groups[service].push(perm);
  }
  return groups;
}

export default function RoleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === "new";

  const [form, setForm] = useState<RoleCreate>({ name: "", description: "", permission_ids: [] });
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const permList = await rbacApi.listPermissions();
      setPermissions(permList);

      if (!isNew && id) {
        const role = await rbacApi.getRole(id);
        setForm({ name: role.name, description: role.description, permission_ids: role.permission_ids });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [id, isNew]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      if (isNew) {
        await rbacApi.createRole(form);
      } else if (id) {
        await rbacApi.updateRole(id, form);
      }
      void navigate("/rbac/roles");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save role");
    } finally {
      setSaving(false);
    }
  };

  const togglePermission = (permissionId: string) => {
    setForm((prev) => ({
      ...prev,
      permission_ids: prev.permission_ids.includes(permissionId)
        ? prev.permission_ids.filter((p) => p !== permissionId)
        : [...prev.permission_ids, permissionId],
    }));
  };

  const grouped = groupPermissionsByService(permissions);

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">{isNew ? "New Role" : "Edit Role"}</h1>
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/rbac/roles" className="rounded-md p-1 text-slate-300 hover:bg-slate-800" aria-label="Back to roles">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-slate-100">{isNew ? "New Role" : "Edit Role"}</h1>
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4 space-y-4">
          <div>
            <label htmlFor="role-name" className="block text-sm font-medium text-slate-300">Name</label>
            <input
              id="role-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label htmlFor="role-description" className="block text-sm font-medium text-slate-300">Description</label>
            <input
              id="role-description"
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              required
            />
          </div>
        </div>

        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
          <h2 className="mb-4 text-lg font-semibold text-slate-100">Permissions</h2>
          <div className="space-y-4">
            {Object.entries(grouped)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([service, perms]) => (
                <div key={service}>
                  <h3 className="mb-2 text-sm font-medium capitalize text-slate-400">{service}</h3>
                  <div className="space-y-1">
                    {perms.map((perm) => (
                      <label key={perm._id} className="flex items-center gap-2 rounded px-2 py-1 hover:bg-slate-800">
                        <input
                          type="checkbox"
                          checked={form.permission_ids.includes(perm._id)}
                          onChange={() => togglePermission(perm._id)}
                          className="rounded"
                        />
                        <span className="text-sm font-mono text-slate-200">{perm.code}</span>
                        <span className="text-xs text-slate-500">— {perm.description}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            {permissions.length === 0 && (
              <p className="text-sm text-slate-400">No permissions available.</p>
            )}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving || !form.name || !form.description}
            className="inline-flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
          >
            <Check className="h-4 w-4" />
            {saving ? "Saving..." : isNew ? "Create Role" : "Save Changes"}
          </button>
          <Link
            to="/rbac/roles"
            className="inline-flex items-center rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
