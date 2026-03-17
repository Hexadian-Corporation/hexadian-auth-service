import type { ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div
      className="relative flex min-h-screen items-center justify-center bg-[#0b0e17] bg-cover bg-center px-4"
      style={{ backgroundImage: "url('/brand/HEXADIAN-Background.png')" }}
    >
      <div className="absolute inset-0 bg-black/85" aria-hidden="true" />
      <div className="relative z-10 w-full max-w-md space-y-8">
        <div className="flex flex-col items-center gap-2">
          <img
            src="/brand/HEXADIAN-Letters.png"
            alt="Hexadian"
            className="h-10 w-auto"
          />
          <p className="text-sm text-slate-400">Authentication Portal</p>
        </div>
        <div className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-8 shadow-lg backdrop-blur-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
