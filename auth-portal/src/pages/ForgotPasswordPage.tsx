import { type FormEvent, useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { forgotPassword, confirmForgotPassword } from "@/api/auth";
import {
  validateForgotPasswordForm,
  validateForgotPasswordResetForm,
  hasErrors,
  type ValidationErrors,
} from "@/lib/validation";

type Step = "identity" | "code" | "reset" | "success";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [step, setStep] = useState<Step>("identity");
  const [username, setUsername] = useState("");
  const [rsiHandle, setRsiHandle] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    if (!verificationCode) return;
    void navigator.clipboard.writeText(verificationCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [verificationCode]);

  async function handleIdentitySubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validateForgotPasswordForm({
      username,
      rsiHandle,
    });
    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    setSubmitting(true);
    try {
      const res = await forgotPassword({
        username,
        rsi_handle: rsiHandle,
      });
      setVerificationCode(res.verification_code);
      setStep("code");
    } catch (err) {
      setApiError(
        err instanceof Error ? err.message : "Request failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResetSubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validateForgotPasswordResetForm({
      newPassword,
      confirmPassword,
    });
    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    setSubmitting(true);
    try {
      await confirmForgotPassword({
        username,
        rsi_handle: rsiHandle,
        new_password: newPassword,
      });
      setStep("success");
      setTimeout(() => {
        const params = searchParams.toString();
        navigate(`/login${params ? `?${params}` : ""}`, { replace: true });
      }, 3000);
    } catch (err) {
      setApiError(
        err instanceof Error ? err.message : "Password reset failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500";
  const errorClass = "mt-1 text-xs text-red-400";
  const buttonClass =
    "w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50";
  const loginPath = `/login${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;

  if (step === "success") {
    return (
      <AuthLayout>
        <div className="text-center">
          <svg
            className="mx-auto mb-4 h-12 w-12 text-emerald-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2 className="mb-2 text-xl font-semibold text-white">
            Password Reset!
          </h2>
          <p role="status" className="text-sm text-slate-400">
            Redirecting to login…
          </p>
        </div>
      </AuthLayout>
    );
  }

  if (step === "code") {
    return (
      <AuthLayout>
        <h2 className="mb-6 text-xl font-semibold text-white">
          RSI Bio Verification
        </h2>

        <p className="mb-4 text-sm text-slate-400">
          Copy this code and paste it into your{" "}
          <a
            href="https://robertsspaceindustries.com/account/profile"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:underline"
          >
            RSI profile bio
          </a>
          .
        </p>

        <div className="mb-6 rounded-lg border border-slate-700 bg-slate-800 p-4">
          <p className="mb-2 text-xs font-medium text-slate-400">
            Verification Code
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 break-all text-sm text-cyan-300">
              {verificationCode}
            </code>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 rounded-md border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs text-slate-300 transition-colors hover:bg-slate-600"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setStep("reset")}
          className={buttonClass}
        >
          I&apos;ve Updated My RSI Bio
        </button>
      </AuthLayout>
    );
  }

  if (step === "reset") {
    return (
      <AuthLayout>
        <h2 className="mb-6 text-xl font-semibold text-white">
          Reset Password
        </h2>

        {apiError && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
          >
            {apiError}
          </div>
        )}

        <form onSubmit={handleResetSubmit} className="space-y-4" noValidate>
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
            {errors.password && (
              <p className={errorClass}>{errors.password}</p>
            )}
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

          <button type="submit" disabled={submitting} className={buttonClass}>
            {submitting ? "Resetting Password…" : "Reset Password"}
          </button>
        </form>
      </AuthLayout>
    );
  }

  // Step: identity (default)
  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">
        Forgot Password
      </h2>

      {apiError && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
        >
          {apiError}
        </div>
      )}

      <form onSubmit={handleIdentitySubmit} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="username"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Username
          </label>
          <input
            id="username"
            type="text"
            required
            className={inputClass}
            placeholder="Enter your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          {errors.username && (
            <p className={errorClass}>{errors.username}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="rsiHandle"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            RSI Handle
          </label>
          <input
            id="rsiHandle"
            type="text"
            required
            className={inputClass}
            placeholder="Enter your RSI handle"
            value={rsiHandle}
            onChange={(e) => setRsiHandle(e.target.value)}
          />
          {errors.rsiHandle && (
            <p className={errorClass}>{errors.rsiHandle}</p>
          )}
        </div>

        <button type="submit" disabled={submitting} className={buttonClass}>
          {submitting ? "Submitting…" : "Continue"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-400">
        <Link to={loginPath} className="text-cyan-400 hover:underline">
          Back to Login
        </Link>
      </p>
    </AuthLayout>
  );
}
