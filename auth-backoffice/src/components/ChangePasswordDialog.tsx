import { type FormEvent, useState } from "react";

interface ChangePasswordDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (oldPassword: string, newPassword: string) => Promise<void>;
}

export default function ChangePasswordDialog({ open, onClose, onSubmit }: ChangePasswordDialogProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!open) return null;

  function validate(): Record<string, string> {
    const errs: Record<string, string> = {};
    if (!currentPassword) errs.currentPassword = "Current password is required";
    if (!newPassword) {
      errs.newPassword = "New password is required";
    } else if (newPassword.length < 8) {
      errs.newPassword = "Password must be at least 8 characters";
    }
    if (!confirmPassword) {
      errs.confirmPassword = "Please confirm your new password";
    } else if (newPassword !== confirmPassword) {
      errs.confirmPassword = "Passwords do not match";
    }
    return errs;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setSubmitting(true);
    try {
      await onSubmit(currentPassword, newPassword);
      setSuccess(true);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Password change failed");
    } finally {
      setSubmitting(false);
    }
  }

  function handleCancel() {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setErrors({});
    setApiError("");
    setSuccess(false);
    onClose();
  }

  if (success) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
          <h2 className="text-lg font-semibold">Change Password</h2>
          <div className="mt-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700" role="status">
            Password changed successfully. You will be redirected to login.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">Change Password</h2>
        <p className="mt-2 text-sm text-gray-600">
          After changing your password, all sessions will be revoked and you will need to log in again.
        </p>

        {apiError && (
          <div className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700" role="alert">
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-3 space-y-3" noValidate>
          <div>
            <label htmlFor="current-password" className="block text-sm font-medium text-gray-700">
              Current Password
            </label>
            <input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter your current password"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            {errors.currentPassword && (
              <p className="mt-1 text-xs text-red-600">{errors.currentPassword}</p>
            )}
          </div>

          <div>
            <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">
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
            {errors.newPassword && (
              <p className="mt-1 text-xs text-red-600">{errors.newPassword}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700">
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your new password"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-red-600">{errors.confirmPassword}</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleCancel}
              disabled={submitting}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "Changing…" : "Change Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
