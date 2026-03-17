export default function LoginPage() {
  return (
    <div
      className="relative flex min-h-screen items-center justify-center bg-[#0f0f0f] bg-cover bg-center px-4"
      style={{ backgroundImage: "url('/brand/hxn_back.jpg')" }}
    >
      <div className="absolute inset-0 bg-black/60" aria-hidden="true" />
      <div className="relative z-10 w-full max-w-md space-y-8">
        <div className="flex flex-col items-center gap-3">
          <img
            src="/brand/HEXADIAN-Background_Round.png"
            alt="Hexadian"
            className="h-20 w-20"
          />
          <p className="text-sm text-[#888888]">Auth Backoffice</p>
        </div>
        <div className="rounded-[14px] border border-white/[0.04] bg-[#1c1c1c] p-8 shadow-[0_10px_30px_rgba(0,0,0,0.45)]">
          <h2 className="mb-4 text-xl font-semibold text-[#e6eef6]">Sign In</h2>
          <p className="text-sm text-[#888888]">
            Sign in to manage users and permissions.
          </p>
          <p className="mt-2 text-xs text-[#555555]">Login form coming soon.</p>
        </div>
      </div>
      <img
        src="/brand/mbtc_black.png"
        alt="MBTC"
        className="fixed bottom-4 right-5 h-[100px] w-[100px]"
      />
    </div>
  );
}
