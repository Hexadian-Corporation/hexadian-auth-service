import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { exchangeCode } from "@/api/auth";
import { storeTokens, redirectToPortal } from "@/lib/auth";

export default function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const code = searchParams.get("code");
  const [error, setError] = useState(code ? "" : "Missing authorization code.");
  const exchanged = useRef(false);

  useEffect(() => {
    if (error) {
      setTimeout(() => redirectToPortal(), 2000);
      return;
    }

    if (exchanged.current || !code) return;
    exchanged.current = true;

    const state = searchParams.get("state");
    const redirectUri = `${window.location.origin}/callback`;
    exchangeCode(code, redirectUri)
      .then(({ access_token, refresh_token }) => {
        storeTokens(access_token, refresh_token);
        const returnPath = state ? decodeURIComponent(state) : "/";
        navigate(returnPath, { replace: true });
      })
      .catch(() => {
        setError("Authentication failed. Please try again.");
        setTimeout(() => redirectToPortal(), 2000);
      });
  }, [error, code, searchParams, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0e17]">
      {error ? (
        <p className="text-sm text-red-400">{error}</p>
      ) : (
        <p className="text-sm text-slate-400">Signing in…</p>
      )}
    </div>
  );
}

