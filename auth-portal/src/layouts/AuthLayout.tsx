import type { ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0b0e17] px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center gap-2">
          <h1 className="text-3xl font-bold tracking-tight text-cyan-400">
            Hexadian
          </h1>
          <p className="text-sm text-slate-400">Authentication Portal</p>
        </div>
        <div className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-8 shadow-lg backdrop-blur-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
