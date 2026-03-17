import { useEffect, useState, useCallback } from "react";
import { Pencil, Trash2, Plus, X, Check } from "lucide-react";
import type { Permission, PermissionCreate } from "@/types/rbac";
import * as rbacApi from "@/api/rbac";

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<PermissionCreate>({ code: "", description: "" });
  const [createForm, setCreateForm] = useState<PermissionCreate>({ code: "", description: "" });
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [roles, setRoles] = useState<{ _id: string; permission_ids: string[] }[]>([]);

  const loadPermissions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [perms, roleList] = await Promise.all([rbacApi.listPermissions(), rbacApi.listRoles()]);
      setPermissions(perms);
      setRoles(roleList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load permissions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPermissions();
  }, [loadPermissions]);

  const handleCreate = async () => {
    try {
      setError(null);
      await rbacApi.createPermission(createForm);
      setCreateForm({ code: "", description: "" });
      setShowCreateForm(false);
      await loadPermissions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create permission");
    }
  };

  const handleUpdate = async (id: string) => {
    try {
      setError(null);
      await rbacApi.updatePermission(id, editForm);
      setEditingId(null);
      await loadPermissions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update permission");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setError(null);
      await rbacApi.deletePermission(id);
      setDeleteConfirmId(null);
      await loadPermissions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete permission");
    }
  };

  const startEdit = (permission: Permission) => {
    setEditingId(permission._id);
    setEditForm({ code: permission.code, description: permission.description });
  };

  const isAssignedToRoles = (permissionId: string) => {
    return roles.some((r) => r.permission_ids.includes(permissionId));
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Permissions</h1>
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Permissions</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center gap-2 rounded-md bg-cyan-600 px-3 py-2 text-sm font-medium text-white hover:bg-cyan-500"
        >
          <Plus className="h-4 w-4" />
          New Permission
        </button>
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="rounded-md border border-slate-700 bg-slate-900/80 p-4" data-testid="create-form">
          <h2 className="mb-3 text-lg font-semibold text-slate-100">Create Permission</h2>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Code (e.g. contracts:read)"
              value={createForm.code}
              onChange={(e) => setCreateForm({ ...createForm, code: e.target.value })}
              className="flex-1 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              aria-label="Permission code"
            />
            <input
              type="text"
              placeholder="Description"
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="flex-1 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
              aria-label="Permission description"
            />
            <button
              onClick={handleCreate}
              disabled={!createForm.code || !createForm.description}
              className="inline-flex items-center gap-1 rounded-md bg-cyan-600 px-3 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              Create
            </button>
            <button
              onClick={() => {
                setShowCreateForm(false);
                setCreateForm({ code: "", description: "" });
              }}
              className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {deleteConfirmId && (
        <div role="dialog" aria-label="Delete confirmation" className="rounded-md border border-red-500/30 bg-red-500/10 p-4">
          <p className="mb-2 text-sm font-medium text-red-400">
            Are you sure you want to delete this permission?
          </p>
          {isAssignedToRoles(deleteConfirmId) && (
            <p className="mb-2 text-sm text-red-400">
              ⚠ This permission is assigned to one or more roles.
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
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">Code</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">Description</th>
              <th className="px-4 py-3 text-right text-xs font-medium tracking-wider text-slate-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {permissions.map((permission) => (
              <tr key={permission._id}>
                {editingId === permission._id ? (
                  <>
                    <td className="px-4 py-3">
                      <input
                        type="text"
                        value={editForm.code}
                        onChange={(e) => setEditForm({ ...editForm, code: e.target.value })}
                        className="w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
                        aria-label="Edit permission code"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <input
                        type="text"
                        value={editForm.description}
                        onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        className="w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
                        aria-label="Edit permission description"
                      />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleUpdate(permission._id)}
                          className="inline-flex items-center gap-1 rounded-md bg-cyan-600 px-2 py-1 text-xs font-medium text-white hover:bg-cyan-500"
                        >
                          <Check className="h-3 w-3" />
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800"
                        >
                          <X className="h-3 w-3" />
                          Cancel
                        </button>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 text-sm font-mono text-slate-100">{permission.code}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{permission.description}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => startEdit(permission)}
                          className="inline-flex items-center gap-1 rounded-md border border-slate-600 px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800"
                          aria-label={`Edit ${permission.code}`}
                        >
                          <Pencil className="h-3 w-3" />
                          Edit
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(permission._id)}
                          className="inline-flex items-center gap-1 rounded-md border border-red-500/30 px-2 py-1 text-xs font-medium text-red-400 hover:bg-red-500/10"
                          aria-label={`Delete ${permission.code}`}
                        >
                          <Trash2 className="h-3 w-3" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {permissions.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-sm text-slate-400">
                  No permissions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
