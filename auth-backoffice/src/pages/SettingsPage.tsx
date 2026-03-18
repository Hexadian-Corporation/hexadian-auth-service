import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "@/api/settings";

export default function SettingsPage() {
  const [defaultRedirectUrl, setDefaultRedirectUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getSettings()
      .then((data) => {
        setDefaultRedirectUrl(data.default_redirect_url);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load settings");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await updateSettings({ default_redirect_url: defaultRedirectUrl });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update settings");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-400">Loading settings…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Settings</h1>

      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400"
        >
          {error}
        </div>
      )}

      {success && (
        <div
          role="status"
          className="rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-400"
        >
          Settings saved successfully.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <div className="space-y-1">
          <label
            htmlFor="default_redirect_url"
            className="block text-sm font-medium text-slate-300"
          >
            Default redirect URL
          </label>
          <input
            id="default_redirect_url"
            type="url"
            value={defaultRedirectUrl}
            onChange={(e) => setDefaultRedirectUrl(e.target.value)}
            required
            className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
            placeholder="https://example.com"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-700 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </form>
    </div>
  );
}
