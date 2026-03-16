import { Link } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";

export default function LoginPage() {
  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">Sign In</h2>
      <p className="text-sm text-slate-400">Login page coming soon.</p>
      <p className="mt-4 text-sm text-slate-400">
        Don&apos;t have an account?{" "}
        <Link to="/register" className="text-cyan-400 hover:underline">
          Register
        </Link>
      </p>
    </AuthLayout>
  );
}
