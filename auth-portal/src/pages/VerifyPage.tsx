import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router";
import AuthLayout from "@/layouts/AuthLayout";
import { startVerification, confirmVerification } from "@/api/auth";
import {
  getAccessToken,
  parseAccessToken,
  storeTokens,
  type AccessTokenPayload,
} from "@/lib/auth";
import { refreshToken as refreshTokenApi } from "@/api/auth";

function VerificationStatus({ verified }: { verified: boolean }) {
  return verified ? (
    <span className="inline-flex items-center rounded-full bg-green-500/20 px-2.5 py-0.5 text-xs font-medium text-green-400">
      Verified
    </span>
  ) : (
    <span className="inline-flex items-center rounded-full bg-slate-500/20 px-2.5 py-0.5 text-xs font-medium text-slate-400">
      Not Verified
    </span>
  );
}

function VerificationCodeDisplay({
  code,
  copied,
  onCopy,
}: {
  code: string;
  copied: boolean;
  onCopy: () => void;
}) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <p className="mb-2 text-xs font-medium text-slate-400">
        Verification Code
      </p>
      <div className="flex items-center gap-2">
        <code className="flex-1 break-all text-sm text-cyan-300">{code}</code>
        <button
          type="button"
          onClick={onCopy}
          className="shrink-0 rounded-md border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs text-slate-300 transition-colors hover:bg-slate-600"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  const navigate = useNavigate();
  const tokenPayload = parseAccessToken();

  const [verificationCode, setVerificationCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [verified, setVerified] = useState(
    () => tokenPayload?.rsi_verified ?? false,
  );

  const rsiHandle = tokenPayload?.rsi_handle ?? null;

  const handleCopy = useCallback(() => {
    if (!verificationCode) return;
    void navigator.clipboard.writeText(verificationCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [verificationCode]);

  useEffect(() => {
    if (!tokenPayload) {
      navigate("/login?redirect_uri=/verify", { replace: true });
    }
  }, [tokenPayload, navigate]);

  if (!tokenPayload) {
    return null;
  }

  async function refreshUserState(): Promise<AccessTokenPayload | null> {
    const refreshTokenValue = localStorage.getItem("refresh_token");
    if (!refreshTokenValue) return null;
    try {
      const tokens = await refreshTokenApi(refreshTokenValue);
      storeTokens(tokens);
      return parseAccessToken();
    } catch {
      return null;
    }
  }

  async function handleStartVerification() {
    if (!rsiHandle) return;
    setError("");
    setSubmitting(true);
    try {
      const token = getAccessToken()!;
      const res = await startVerification({ rsi_handle: rsiHandle }, token);
      if (res.verified) {
        setVerified(true);
      } else if (res.verification_code) {
        setVerificationCode(res.verification_code);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start verification",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirmVerification() {
    if (!rsiHandle) return;
    setError("");
    setSubmitting(true);
    try {
      const token = getAccessToken()!;
      const res = await confirmVerification({ rsi_handle: rsiHandle }, token);
      if (res.verified) {
        setVerified(true);
        setVerificationCode(null);
        await refreshUserState();
      } else {
        setError(
          "Code not found in your RSI profile bio. Make sure you saved your profile.",
        );
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Verification failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const buttonClass =
    "w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <AuthLayout>
      <h2 className="mb-6 text-xl font-semibold text-white">
        RSI Verification
      </h2>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
        >
          {error}
        </div>
      )}

      {/* Current status section */}
      <div className="mb-6 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">RSI Handle</span>
          {rsiHandle ? (
            <a
              href={`https://robertsspaceindustries.com/citizens/${rsiHandle}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-cyan-400 hover:underline"
            >
              {rsiHandle}
            </a>
          ) : (
            <span className="text-sm text-slate-500">Not set</span>
          )}
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Status</span>
          <VerificationStatus verified={verified} />
        </div>
      </div>

      {/* Verification flow */}
      {!verified && rsiHandle && (
        <div className="space-y-4">
          {!verificationCode ? (
            <button
              type="button"
              disabled={submitting}
              onClick={handleStartVerification}
              className={buttonClass}
            >
              {submitting ? "Starting…" : "Start Verification"}
            </button>
          ) : (
            <>
              <VerificationCodeDisplay
                code={verificationCode}
                copied={copied}
                onCopy={handleCopy}
              />

              <p className="text-xs text-slate-400">
                Copy this code and paste it into your{" "}
                <a
                  href="https://robertsspaceindustries.com/account/profile"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-400 hover:underline"
                >
                  RSI profile bio
                </a>
                .
              </p>

              <button
                type="button"
                disabled={submitting}
                onClick={handleConfirmVerification}
                className={buttonClass}
              >
                {submitting ? "Confirming…" : "Confirm Verification"}
              </button>
            </>
          )}
        </div>
      )}

      {verified && (
        <p className="text-sm text-slate-400">
          Your RSI identity has been verified.
        </p>
      )}
    </AuthLayout>
  );
}
