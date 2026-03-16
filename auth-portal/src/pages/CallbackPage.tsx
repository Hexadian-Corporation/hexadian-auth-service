import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { exchangeCode } from "@/api/auth";
import { storeTokens } from "@/lib/auth";

export default function CallbackPage() {
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code");
  const redirectUri = window.location.origin + "/callback";

  const [error, setError] = useState(() =>
    code ? "" : "Missing authorization code",
  );

  useEffect(() => {
    if (!code) return;

    let cancelled = false;

    async function exchange() {
      try {
        const tokens = await exchangeCode({
          code: code!,
          redirect_uri: redirectUri,
        });
        if (!cancelled) {
          storeTokens(tokens);
          window.location.href = "/";
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Token exchange failed",
          );
        }
      }
    }

    void exchange();

    return () => {
      cancelled = true;
    };
  }, [code, redirectUri]);

  if (error) {
    return (
      <AuthLayout>
        <h2 className="mb-6 text-xl font-semibold text-white">Error</h2>
        <div
          role="alert"
          className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
        >
          {error}
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">Processing...</h2>
      <p className="text-sm text-slate-400">
        Exchanging authorization code for token.
      </p>
    </AuthLayout>
  );
}
