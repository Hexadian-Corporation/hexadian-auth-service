import type { PortalSettings, PortalSettingsUpdate } from "@/types/settings";
import { authFetch } from "@/lib/auth";

const API_BASE = "/api/auth";

export async function getSettings(): Promise<PortalSettings> {
  const response = await authFetch(`${API_BASE}/settings`);
  if (!response.ok) {
    throw new Error(`Failed to get settings: ${response.statusText}`);
  }
  return response.json() as Promise<PortalSettings>;
}

export async function updateSettings(data: PortalSettingsUpdate): Promise<PortalSettings> {
  const response = await authFetch(`${API_BASE}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`);
  }
  return response.json() as Promise<PortalSettings>;
}
