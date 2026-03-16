import { Link } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";

export default function RegisterPage() {
  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">
        Create Account
      </h2>
      <p className="text-sm text-slate-400">Registration page coming soon.</p>
      <p className="mt-4 text-sm text-slate-400">
        Already have an account?{" "}
        <Link to="/login" className="text-cyan-400 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
