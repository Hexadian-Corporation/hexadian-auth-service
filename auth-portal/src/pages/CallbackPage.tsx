import AuthLayout from "@/layouts/AuthLayout";

export default function CallbackPage() {
  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">
        Processing...
      </h2>
      <p className="text-sm text-slate-400">
        Exchanging authorization code for token.
      </p>
    </AuthLayout>
  );
}
