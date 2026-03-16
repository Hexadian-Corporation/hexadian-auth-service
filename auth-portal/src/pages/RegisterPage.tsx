import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { register } from "@/api/auth";
import {
  validateRegistrationForm,
  hasErrors,
  type ValidationErrors,
} from "@/lib/validation";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [rsiHandle, setRsiHandle] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validateRegistrationForm({
      username,
      password,
      confirmPassword,
      rsiHandle,
    });

    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    setSubmitting(true);
    try {
      await register({ username, password, rsi_handle: rsiHandle });
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500";
  const errorClass = "mt-1 text-xs text-red-400";

  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">Create Account</h2>

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
          {errors.username && <p className={errorClass}>{errors.username}</p>}
        </div>

        <div>
          <label
            htmlFor="password"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            className={inputClass}
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {errors.password && <p className={errorClass}>{errors.password}</p>}
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            required
            className={inputClass}
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {errors.confirmPassword && (
            <p className={errorClass}>{errors.confirmPassword}</p>
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
            pattern="^[A-Za-z0-9_-]{3,30}$"
            className={inputClass}
            placeholder="Your Star Citizen handle"
            value={rsiHandle}
            onChange={(e) => setRsiHandle(e.target.value)}
          />
          {errors.rsiHandle && (
            <p className={errorClass}>{errors.rsiHandle}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating Account…" : "Create Account"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-400">
        Already have an account?{" "}
        <Link to="/login" className="text-cyan-400 hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
