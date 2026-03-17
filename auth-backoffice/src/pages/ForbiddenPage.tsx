import { clearTokens, redirectToPortal } from "@/lib/auth";

export default function ForbiddenPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center bg-[#0f0f0f] text-center">
      <h1 className="text-6xl font-bold text-[#e6eef6]">403</h1>
      <p className="mt-4 text-lg text-[#888888]">
        You don&apos;t have permission to access this application.
      </p>
      <p className="mt-1 text-sm text-[#555555]">
        Contact an administrator to request access.
      </p>
      <button
        onClick={() => {
          clearTokens();
          redirectToPortal();
        }}
        className="mt-8 rounded-md bg-[#242424] px-6 py-2 text-sm font-medium text-[#e6eef6] transition-colors hover:bg-[#2a2a2a]"
      >
        Log out
      </button>
    </div>
  );
}
