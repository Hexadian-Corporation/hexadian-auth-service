import { type FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { login, authorize } from "@/api/auth";
import { validateLoginForm, hasErrors, type ValidationErrors } from "@/lib/validation";
import { storeTokens } from "@/lib/auth";

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const redirectUri = searchParams.get("redirect_uri");
  const state = searchParams.get("state") ?? "";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setApiError("");

    const validationErrors = validateLoginForm({ username, password });
    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    setSubmitting(true);
    try {
      if (redirectUri) {
        const res = await authorize({
          username,
          password,
          redirect_uri: redirectUri,
          state,
        });
        const url = new URL(res.redirect_uri);
        url.searchParams.set("code", res.code);
        url.searchParams.set("state", res.state);
        window.location.href = url.toString();
      } else {
        const tokens = await login({ username, password });
        storeTokens(tokens);
        window.location.href = "/";
      }
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500";
  const errorClass = "mt-1 text-xs text-red-400";

  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">Sign In</h2>

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
            className={inputClass}
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {errors.password && <p className={errorClass}>{errors.password}</p>}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Signing In…" : "Sign In"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-400">
        Don&apos;t have an account?{" "}
        <Link to="/register" className="text-cyan-400 hover:underline">
          Register
        </Link>
      </p>
    </AuthLayout>
  );
}
