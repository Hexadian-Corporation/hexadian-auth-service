import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { ArrowLeft, Check, X } from "lucide-react";
import type { Role, Permission, GroupCreate } from "@/types/rbac";
import * as rbacApi from "@/api/rbac";

export default function GroupDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === "new";

  const [form, setForm] = useState<GroupCreate>({ name: "", description: "", role_ids: [], auto_assign_apps: [] });
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [members, setMembers] = useState<{ _id: string; username: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appInput, setAppInput] = useState("");
  const [appInputError, setAppInputError] = useState<string | null>(null);

  const addApp = () => {
    const value = appInput.trim();
    setAppInputError(null);
    if (!value) return;
    if (!/^[A-Za-z0-9-]+$/.test(value)) {
      setAppInputError("Only alphanumeric characters and hyphens are allowed.");
      return;
    }
    if (form.auto_assign_apps.includes(value)) {
      setAppInputError("This app identifier is already added.");
      return;
    }
    setForm((prev) => ({ ...prev, auto_assign_apps: [...prev.auto_assign_apps, value] }));
    setAppInput("");
  };

  const removeApp = (app: string) => {
    setForm((prev) => ({ ...prev, auto_assign_apps: prev.auto_assign_apps.filter((a) => a !== app) }));
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [roleList, permList, users] = await Promise.all([
        rbacApi.listRoles(),
        rbacApi.listPermissions(),
        rbacApi.listUsers(),
      ]);
      setRoles(roleList);
      setPermissions(permList);

      if (!isNew && id) {
        const group = await rbacApi.getGroup(id);
        setForm({ name: group.name, description: group.description, role_ids: group.role_ids, auto_assign_apps: group.auto_assign_apps ?? [] });
        setMembers(users.filter((u) => u.group_ids.includes(id)));
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
        await rbacApi.createGroup(form);
      } else if (id) {
        await rbacApi.updateGroup(id, form);
      }
      void navigate("/rbac/groups");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save group");
    } finally {
      setSaving(false);
    }
  };

  const toggleRole = (roleId: string) => {
    setForm((prev) => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId)
        ? prev.role_ids.filter((r) => r !== roleId)
        : [...prev.role_ids, roleId],
    }));
  };

  const effectivePermissions = useMemo(() => {
    const permIds = new Set<string>();
    for (const role of roles) {
      if (form.role_ids.includes(role._id)) {
        for (const pid of role.permission_ids) {
          permIds.add(pid);
        }
      }
    }
    return permissions.filter((p) => permIds.has(p._id));
  }, [form.role_ids, roles, permissions]);

  const getRolePermissions = (roleId: string): string[] => {
    const role = roles.find((r) => r._id === roleId);
    if (!role) return [];
    return role.permission_ids
      .map((pid) => permissions.find((p) => p._id === pid)?.code)
      .filter((c): c is string => c !== undefined);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">{isNew ? "New Group" : "Edit Group"}</h1>
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/rbac/groups" className="rounded-md p-1 text-slate-300 hover:bg-slate-800" aria-label="Back to groups">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-slate-100">{isNew ? "New Group" : "Edit Group"}</h1>
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4 space-y-4">
          <div>
            <label htmlFor="group-name" className="block text-sm font-medium text-slate-300">Name</label>
            <input
              id="group-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label htmlFor="group-description" className="block text-sm font-medium text-slate-300">Description</label>
            <input
              id="group-description"
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300">Application Auto-Assignment</label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={appInput}
                onChange={(e) => { setAppInput(e.target.value); setAppInputError(null); }}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addApp(); } }}
                className="flex-1 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
                placeholder="e.g. hhh-frontend"
                aria-label="App identifier"
              />
              <button
                type="button"
                onClick={addApp}
                className="rounded-md border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
              >
                Add
              </button>
            </div>
            {appInputError && (
              <p className="mt-1 text-xs text-red-400">{appInputError}</p>
            )}
            {form.auto_assign_apps.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {form.auto_assign_apps.map((app) => (
                  <span
                    key={app}
                    className="inline-flex items-center gap-1 rounded-full bg-slate-700 px-3 py-1 text-sm text-cyan-400"
                  >
                    {app}
                    <button
                      type="button"
                      onClick={() => removeApp(app)}
                      className="rounded-full p-0.5 hover:bg-slate-600"
                      aria-label={`Remove ${app}`}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            <p className="mt-1 text-xs text-slate-400">App IDs that auto-assign this group on registration.</p>
          </div>
        </div>

        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
          <h2 className="mb-4 text-lg font-semibold text-slate-100">Roles</h2>
          <div className="space-y-2">
            {roles.map((role) => {
              const roleCodes = getRolePermissions(role._id);
              return (
                <label key={role._id} className="flex items-start gap-2 rounded px-2 py-1 hover:bg-slate-800">
                  <input
                    type="checkbox"
                    checked={form.role_ids.includes(role._id)}
                    onChange={() => toggleRole(role._id)}
                    className="mt-0.5 rounded"
                  />
                  <div>
                    <span className="text-sm font-medium text-slate-200">{role.name}</span>
                    <span className="ml-2 text-xs text-slate-500">— {role.description}</span>
                    {roleCodes.length > 0 && (
                      <div className="mt-0.5 text-xs text-slate-500">
                        Permissions: {roleCodes.join(", ")}
                      </div>
                    )}
                  </div>
                </label>
              );
            })}
            {roles.length === 0 && (
              <p className="text-sm text-slate-400">No roles available.</p>
            )}
          </div>
        </div>

        {!isNew && members.length > 0 && (
          <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
            <h2 className="mb-3 text-lg font-semibold text-slate-100">Members</h2>
            <ul className="space-y-1">
              {members.map((user) => (
                <li key={user._id} className="text-sm text-slate-300">{user.username}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4">
          <h2 className="mb-3 text-lg font-semibold text-slate-100">Effective Permissions</h2>
          {effectivePermissions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {effectivePermissions.map((perm) => (
                <span
                  key={perm._id}
                  className="inline-block rounded-full bg-slate-700 px-2.5 py-0.5 text-xs font-mono text-slate-300"
                >
                  {perm.code}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No permissions resolved from selected roles.</p>
          )}
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving || !form.name || !form.description}
            className="inline-flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
          >
            <Check className="h-4 w-4" />
            {saving ? "Saving..." : isNew ? "Create Group" : "Save Changes"}
          </button>
          <Link
            to="/rbac/groups"
            className="inline-flex items-center rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
