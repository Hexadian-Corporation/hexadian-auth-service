import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { CheckCircle2, Pencil, Search, Trash2 } from "lucide-react";
import type { User } from "@/types/user";
import type { Group } from "@/types/rbac";
import { listUsers, deleteUser } from "@/api/users";
import { listGroups } from "@/api/rbac";

export default function UsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([listUsers(), listGroups()])
      .then(([usersData, groupsData]) => {
        setUsers(usersData);
        setGroups(groupsData);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load data");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  function getGroupName(groupId: string): string {
    return groups.find((g) => g._id === groupId)?.name ?? groupId;
  }

  const filteredUsers = users.filter((user) => {
    const term = search.toLowerCase();
    return (
      user.username.toLowerCase().includes(term) ||
      user.rsi_handle.toLowerCase().includes(term)
    );
  });

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteUser(deleteTarget._id);
      setUsers((prev) => prev.filter((u) => u._id !== deleteTarget._id));
      setDeleteTarget(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete user",
      );
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Users</h1>
        <p className="text-slate-400">Loading users…</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Users</h1>
      </div>

      {error && (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="relative">
        <Search className="absolute top-2.5 left-3 h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder="Filter by username or RSI handle…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-md border border-slate-700 bg-slate-800 py-2 pr-3 pl-9 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
        />
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                Username
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                RSI Handle
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                RSI Verified
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                Groups
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                Active
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium tracking-wider text-slate-400 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {filteredUsers.map((user) => (
              <tr key={user._id} className="hover:bg-slate-800/50">
                <td className="px-4 py-3 text-sm font-medium text-slate-100 whitespace-nowrap">
                  {user.username}
                </td>
                <td className="px-4 py-3 text-sm whitespace-nowrap text-slate-300">
                  {user.rsi_handle || "—"}
                </td>
                <td className="px-4 py-3 text-sm whitespace-nowrap">
                  {user.rsi_verified ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-green-500/20 px-2 py-0.5 text-xs font-medium text-green-400">
                      <CheckCircle2 className="h-3 w-3" /> Verified
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-slate-700 px-2 py-0.5 text-xs font-medium text-slate-300">
                      Unverified
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex flex-wrap gap-1">
                    {user.group_ids.map((gid) => (
                      <span
                        key={gid}
                        className="inline-flex rounded-full bg-cyan-500/20 px-2 py-0.5 text-xs font-medium text-cyan-400"
                      >
                        {getGroupName(gid)}
                      </span>
                    ))}
                    {user.group_ids.length === 0 && (
                      <span className="text-slate-500">None</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm whitespace-nowrap">
                  {user.is_active ? (
                    <span className="inline-flex rounded-full bg-green-500/20 px-2 py-0.5 text-xs font-medium text-green-400">
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400">
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/users/${user._id}`)}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-cyan-400 hover:bg-cyan-500/10"
                      title="View / Edit"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteTarget(user)}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-red-400 hover:bg-red-500/10"
                      title="Delete user"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredUsers.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-sm text-slate-400"
                >
                  {search ? "No users match your filter." : "No users found."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Delete confirmation dialog */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-sm rounded-lg border border-slate-700 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-slate-100">Delete User</h2>
            <p className="mt-2 text-sm text-slate-300">
              Are you sure you want to delete{" "}
              <strong>{deleteTarget.username}</strong>? This action cannot be
              undone.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setDeleteTarget(null)}
                disabled={deleting}
                className="rounded-md border border-slate-600 px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
