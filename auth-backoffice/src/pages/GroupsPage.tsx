import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router";
import { Trash2, Plus, Pencil } from "lucide-react";
import type { Group } from "@/types/rbac";
import * as rbacApi from "@/api/rbac";

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [memberCounts, setMemberCounts] = useState<Record<string, number>>({});

  const loadGroups = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [groupList, users] = await Promise.all([rbacApi.listGroups(), rbacApi.listUsers()]);
      setGroups(groupList);

      const counts: Record<string, number> = {};
      for (const group of groupList) {
        counts[group._id] = users.filter((u) => u.group_ids.includes(group._id)).length;
      }
      setMemberCounts(counts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load groups");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGroups();
  }, [loadGroups]);

  const handleDelete = async (id: string) => {
    try {
      setError(null);
      await rbacApi.deleteGroup(id);
      setDeleteConfirmId(null);
      await loadGroups();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete group");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Groups</h1>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Groups</h1>
        <Link
          to="/rbac/groups/new"
          className="inline-flex items-center gap-2 rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          <Plus className="h-4 w-4" />
          New Group
        </Link>
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {deleteConfirmId && (
        <div role="dialog" aria-label="Delete confirmation" className="rounded-md border border-red-200 bg-red-50 p-4">
          <p className="mb-2 text-sm font-medium text-red-800">
            Are you sure you want to delete this group?
          </p>
          {(memberCounts[deleteConfirmId] ?? 0) > 0 && (
            <p className="mb-2 text-sm text-red-600">
              ⚠ This group has {memberCounts[deleteConfirmId]} member(s).
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
              className="rounded-md border px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-md border bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">Description</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">Roles</th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase">Members</th>
              <th className="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {groups.map((group) => (
              <tr key={group._id}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{group.name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{group.description}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{group.role_ids.length}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{memberCounts[group._id] ?? 0}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <Link
                      to={`/rbac/groups/${group._id}`}
                      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      <Pencil className="h-3 w-3" />
                      Edit
                    </Link>
                    <button
                      onClick={() => setDeleteConfirmId(group._id)}
                      className="inline-flex items-center gap-1 rounded-md border border-red-200 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                      aria-label={`Delete ${group.name}`}
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {groups.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">
                  No groups found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
