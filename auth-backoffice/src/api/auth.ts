import type { TokenResponse } from "@/lib/auth";
import { authFetch } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_AUTH_API_URL ?? "/api/auth";

export interface LoginRequest {
  username: string;
  password: string;
}

export async function exchangeCode(
  code: string,
  redirectUri: string,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/token/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  });
  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }
  return response.json() as Promise<TokenResponse>;
}

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    throw new Error(`Login failed: ${response.statusText}`);
  }
  return response.json() as Promise<TokenResponse>;
}

export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/token/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.statusText}`);
  }
  return response.json() as Promise<TokenResponse>;
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const response = await authFetch(`${API_BASE}/password/change`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Password change failed");
  }
}
