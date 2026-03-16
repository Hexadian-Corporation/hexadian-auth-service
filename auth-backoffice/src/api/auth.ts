import type { LoginRequest, LoginResponse } from "@/types/auth";

const API_BASE = "/api/auth";

export async function exchangeCode(
  code: string,
  redirectUri: string,
): Promise<{ access_token: string; refresh_token: string }> {
  const response = await fetch(`${API_BASE}/token/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  });
  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.statusText}`);
  }
  return response.json() as Promise<{ access_token: string; refresh_token: string }>;
}

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    throw new Error(`Login failed: ${response.statusText}`);
  }
  return response.json() as Promise<LoginResponse>;
}

export async function refreshToken(): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.statusText}`);
  }
  return response.json() as Promise<LoginResponse>;
}
