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

  const inputClass =
    "mt-1 w-full rounded-[10px] border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-sm text-[#e6eef6] placeholder-[#555555] focus:border-white/[0.15] focus:ring-1 focus:ring-white/[0.15] focus:outline-none";

  if (success) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
        <div className="w-full max-w-sm rounded-[14px] border border-white/[0.04] bg-[#1c1c1c] p-6 shadow-[0_10px_30px_rgba(0,0,0,0.45)]">
          <h2 className="text-lg font-semibold text-[#e6eef6]">Change Password</h2>
          <div className="mt-2 rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-400" role="status">
            Password changed successfully. You will be redirected to login.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-sm rounded-[14px] border border-white/[0.04] bg-[#1c1c1c] p-6 shadow-[0_10px_30px_rgba(0,0,0,0.45)]">
        <h2 className="text-lg font-semibold text-[#e6eef6]">Change Password</h2>
        <p className="mt-2 text-sm text-[#888888]">
          After changing your password, all sessions will be revoked and you will need to log in again.
        </p>

        {apiError && (
          <div className="mt-2 rounded-md border border-red-500/30 bg-red-500/10 p-2 text-sm text-red-400" role="alert">
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-3 space-y-3" noValidate>
          <div>
            <label htmlFor="current-password" className="block text-sm font-medium text-[#e6eef6]">
              Current Password
            </label>
            <input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter your current password"
              className={inputClass}
            />
            {errors.currentPassword && (
              <p className="mt-1 text-xs text-red-400">{errors.currentPassword}</p>
            )}
          </div>

          <div>
            <label htmlFor="new-password" className="block text-sm font-medium text-[#e6eef6]">
              New Password
            </label>
            <input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className={inputClass}
            />
            {errors.newPassword && (
              <p className="mt-1 text-xs text-red-400">{errors.newPassword}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-sm font-medium text-[#e6eef6]">
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your new password"
              className={inputClass}
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-red-400">{errors.confirmPassword}</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleCancel}
              disabled={submitting}
              className="rounded-[10px] border border-white/[0.08] bg-[rgba(40,40,40,0.6)] px-3 py-1.5 text-sm font-semibold text-[#e6eef6] transition-colors hover:bg-[rgba(30,30,30,0.8)] disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-[10px] border border-white/[0.08] bg-[rgba(40,40,40,0.6)] px-3 py-1.5 text-sm font-semibold text-[#e6eef6] transition-colors hover:bg-[rgba(30,30,30,0.8)] disabled:opacity-50"
            >
              {submitting ? "Changing…" : "Change Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
