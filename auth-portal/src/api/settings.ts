const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL ?? "http://localhost:8006";

export function getPortalRedirect(): Promise<{ default_redirect_url: string }> {
  return fetch(`${AUTH_API_URL}/settings/portal`, {
    headers: { "Content-Type": "application/json" },
  }).then(async (res) => {
    if (!res.ok) {
      throw new Error(`Request failed: ${res.status}`);
    }
    return res.json() as Promise<{ default_redirect_url: string }>;
  });
}
