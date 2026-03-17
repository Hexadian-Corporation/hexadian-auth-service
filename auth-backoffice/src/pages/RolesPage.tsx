import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router";
import { Trash2, Plus, Pencil } from "lucide-react";
import type { Role } from "@/types/rbac";
import * as rbacApi from "@/api/rbac";

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [groups, setGroups] = useState<{ _id: string; role_ids: string[] }[]>([]);

  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [roleList, groupList] = await Promise.all([rbacApi.listRoles(), rbacApi.listGroups()]);
      setRoles(roleList);
      setGroups(groupList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load roles");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRoles();
  }, [loadRoles]);

  const handleDelete = async (id: string) => {
    try {
      setError(null);
      await rbacApi.deleteRole(id);
      setDeleteConfirmId(null);
      await loadRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete role");
    }
  };

  const isAssignedToGroups = (roleId: string) => {
    return groups.some((g) => g.role_ids.includes(roleId));
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Roles</h1>
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Roles</h1>
        <Link
          to="/rbac/roles/new"
          className="inline-flex items-center gap-2 rounded-md bg-cyan-600 px-3 py-2 text-sm font-medium text-white hover:bg-cyan-500"
        >
          <Plus className="h-4 w-4" />
          New Role
        </Link>
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {deleteConfirmId && (
        <div role="dialog" aria-label="Delete confirmation" className="rounded-md border border-red-500/30 bg-red-500/10 p-4">
          <p className="mb-2 text-sm font-medium text-red-400">
            Are you sure you want to delete this role?
          </p>
          {isAssignedToGroups(deleteConfirmId) && (
            <p className="mb-2 text-sm text-red-400">
              ⚠ This role is assigned to one or more groups.
            </p>
          )}
          <div className="flex gap-2">
            <button
              onClick={() => handleDelete(deleteConfirmId)}
              className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
            >
              Confirm Delete
            </button>
            <button
              onClick={() => setDeleteConfirmId(null)}
              className="rounded-md border border-slate-600 px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-md border border-slate-700 bg-slate-900/80">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">Description</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">Permissions</th>
              <th className="px-4 py-3 text-right text-xs font-medium tracking-wider text-slate-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {roles.map((role) => (
              <tr key={role._id}>
                <td className="px-4 py-3 text-sm font-medium text-slate-100">{role.name}</td>
                <td className="px-4 py-3 text-sm text-slate-300">{role.description}</td>
                <td className="px-4 py-3 text-sm text-slate-300">{role.permission_ids.length}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <Link
                      to={`/rbac/roles/${role._id}`}
                      className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800"
                    >
                      <Pencil className="h-3 w-3" />
                      Edit
                    </Link>
                    <button
                      onClick={() => setDeleteConfirmId(role._id)}
                      className="inline-flex items-center gap-1 rounded-md border border-red-500/30 px-2 py-1 text-xs font-medium text-red-400 hover:bg-red-500/10"
                      aria-label={`Delete ${role.name}`}
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {roles.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-sm text-slate-400">
                  No roles found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
