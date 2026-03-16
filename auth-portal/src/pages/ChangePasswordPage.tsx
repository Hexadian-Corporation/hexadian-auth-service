import { type FormEvent, useState, useEffect } from "react";
import { useNavigate } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { changePassword } from "@/api/auth";
import {
  validateChangePasswordForm,
  hasErrors,
  type ValidationErrors,
} from "@/lib/validation";
import { parseAccessToken, getAccessToken, clearTokens } from "@/lib/auth";

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const tokenPayload = parseAccessToken();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!tokenPayload) {
      navigate("/login", { replace: true });
    }
  }, [tokenPayload, navigate]);

  if (!tokenPayload) {
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validateChangePasswordForm({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    setSubmitting(true);
    try {
      const token = getAccessToken()!;
      await changePassword(
        { old_password: currentPassword, new_password: newPassword },
        token,
      );
      setSuccess(true);
      clearTokens();
      setTimeout(() => {
        navigate("/login", { replace: true });
      }, 3000);
    } catch (err) {
      setApiError(
        err instanceof Error ? err.message : "Failed to change password",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500";
  const errorClass = "mt-1 text-xs text-red-400";

  if (success) {
    return (
      <AuthLayout>
        <h2 className="mb-6 text-xl font-semibold text-white">
          Change Password
        </h2>
        <div
          role="status"
          className="rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-400"
        >
          Password changed successfully. You will be redirected to the login
          page.
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">
        Change Password
      </h2>

      <p className="mb-4 text-xs text-slate-400">
        After changing your password, all sessions will be revoked and you will
        need to log in again.
      </p>

      {apiError && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
        >
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="currentPassword"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Current Password
          </label>
          <input
            id="currentPassword"
            type="password"
            required
            className={inputClass}
            placeholder="Enter your current password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          {errors.currentPassword && (
            <p className={errorClass}>{errors.currentPassword}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="newPassword"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            New Password
          </label>
          <input
            id="newPassword"
            type="password"
            required
            className={inputClass}
            placeholder="Enter your new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          {errors.password && <p className={errorClass}>{errors.password}</p>}
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Confirm New Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            required
            className={inputClass}
            placeholder="Confirm your new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {errors.confirmPassword && (
            <p className={errorClass}>{errors.confirmPassword}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Changing Password…" : "Change Password"}
        </button>
      </form>
    </AuthLayout>
  );
}
