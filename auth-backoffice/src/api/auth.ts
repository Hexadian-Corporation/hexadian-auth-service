import type { LoginRequest, LoginResponse } from "@/types/auth";

const API_BASE = "/api/auth";

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
