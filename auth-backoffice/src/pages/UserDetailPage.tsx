import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import { ArrowLeft, KeyRound, Save, Trash2, X } from "lucide-react";
import type { User, UserUpdate } from "@/types/user";
import type { Group } from "@/types/rbac";
import { getUser, updateUser, deleteUser, resetPassword } from "@/api/users";
import { listGroups, assignUserGroup, removeUserGroup } from "@/api/rbac";

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [user, setUser] = useState<User | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Edit form state
  const [username, setUsername] = useState("");
  const [rsiHandle, setRsiHandle] = useState("");

  // Dialog state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [resettingPassword, setResettingPassword] = useState(false);

  // Group management state
  const [addGroupId, setAddGroupId] = useState("");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);

    Promise.all([getUser(id), listGroups()])
      .then(([userData, groupsData]) => {
        setUser(userData);
        setGroups(groupsData);
        setUsername(userData.username);
        setRsiHandle(userData.rsi_handle);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load user");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  function getGroupName(groupId: string): string {
    return groups.find((g) => g._id === groupId)?.name ?? groupId;
  }

  function availableGroups(): Group[] {
    if (!user) return [];
    return groups.filter((g) => !user.group_ids.includes(g._id));
  }

  async function handleSave() {
    if (!id || !user) return;
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const updates: UserUpdate = {};
      if (username !== user.username) updates.username = username;
      if (rsiHandle !== user.rsi_handle) updates.rsi_handle = rsiHandle;

      if (Object.keys(updates).length > 0) {
        const updated = await updateUser(id, updates);
        setUser(updated);
        setUsername(updated.username);
        setRsiHandle(updated.rsi_handle);
      }
      setSuccessMessage("User updated successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!id) return;
    setDeleting(true);
    try {
      await deleteUser(id);
      navigate("/users");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete user");
      setShowDeleteDialog(false);
    } finally {
      setDeleting(false);
    }
  }

  async function handleResetPassword() {
    if (!id) return;
    setPasswordError(null);
    if (newPassword.length < 8) {
      setPasswordError("Password must be at least 8 characters");
      return;
    }
    setResettingPassword(true);
    try {
      await resetPassword(id, newPassword);
      setShowPasswordDialog(false);
      setNewPassword("");
      setSuccessMessage("Password reset successfully");
    } catch (err) {
      setPasswordError(
        err instanceof Error ? err.message : "Failed to reset password",
      );
    } finally {
      setResettingPassword(false);
    }
  }

  async function handleAddGroup() {
    if (!id || !addGroupId) return;
    setError(null);
    try {
      await assignUserGroup(id, addGroupId);
      setUser((prev) =>
        prev ? { ...prev, group_ids: [...prev.group_ids, addGroupId] } : prev,
      );
      setAddGroupId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add group");
    }
  }

  async function handleRemoveGroup(groupId: string) {
    if (!id) return;
    setError(null);
    try {
      await removeUserGroup(id, groupId);
      setUser((prev) =>
        prev
          ? { ...prev, group_ids: prev.group_ids.filter((g) => g !== groupId) }
          : prev,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove group");
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">User Detail</h1>
        <p className="text-gray-500">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">User Detail</h1>
        <p className="text-red-600">{error ?? "User not found"}</p>
        <button
          onClick={() => navigate("/users")}
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Users
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/users")}
          className="rounded-md p-1 hover:bg-gray-100"
          title="Back to users"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-bold">Edit User</h1>
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => setShowPasswordDialog(true)}
            className="inline-flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <KeyRound className="h-4 w-4" />
            Reset Password
          </button>
          <button
            onClick={() => setShowDeleteDialog(true)}
            className="inline-flex items-center gap-1 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          {successMessage}
        </div>
      )}

      {/* Edit form */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">User Information</h2>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="rsi-handle"
              className="block text-sm font-medium text-gray-700"
            >
              RSI Handle
            </label>
            <input
              id="rsi-handle"
              type="text"
              value={rsiHandle}
              onChange={(e) => setRsiHandle(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-gray-500">
              Changing the RSI handle will reset RSI verification.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div>
              <span className="block text-sm font-medium text-gray-700">
                Active
              </span>
              {user.is_active ? (
                <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  Active
                </span>
              ) : (
                <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                  Inactive
                </span>
              )}
            </div>
            <div>
              <span className="block text-sm font-medium text-gray-700">
                RSI Verified
              </span>
              {user.rsi_verified ? (
                <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  Verified
                </span>
              ) : (
                <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                  Unverified
                </span>
              )}
            </div>
          </div>
          <div className="pt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </div>

      {/* Group management */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Groups</h2>
        <div className="space-y-3">
          {user.group_ids.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {user.group_ids.map((gid) => (
                <span
                  key={gid}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700"
                >
                  {getGroupName(gid)}
                  <button
                    onClick={() => handleRemoveGroup(gid)}
                    className="ml-1 rounded-full p-0.5 hover:bg-blue-200"
                    title={`Remove ${getGroupName(gid)}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No groups assigned.</p>
          )}
          {availableGroups().length > 0 && (
            <div className="flex items-center gap-2">
              <select
                value={addGroupId}
                onChange={(e) => setAddGroupId(e.target.value)}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              >
                <option value="">Add group…</option>
                {availableGroups().map((g) => (
                  <option key={g._id} value={g._id}>
                    {g.name}
                  </option>
                ))}
              </select>
              <button
                onClick={handleAddGroup}
                disabled={!addGroupId}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Add
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold">Delete User</h2>
            <p className="mt-2 text-sm text-gray-600">
              Are you sure you want to delete{" "}
              <strong>{user.username}</strong>? This action cannot be undone.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteDialog(false)}
                disabled={deleting}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
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

      {/* Password reset dialog */}
      {showPasswordDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold">Reset Password</h2>
            <p className="mt-2 text-sm text-gray-600">
              Set a new password for <strong>{user.username}</strong>.
            </p>
            {passwordError && (
              <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">
                {passwordError}
              </div>
            )}
            <div className="mt-3">
              <label
                htmlFor="new-password"
                className="block text-sm font-medium text-gray-700"
              >
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowPasswordDialog(false);
                  setNewPassword("");
                  setPasswordError(null);
                }}
                disabled={resettingPassword}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleResetPassword}
                disabled={resettingPassword}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {resettingPassword ? "Resetting…" : "Reset Password"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
