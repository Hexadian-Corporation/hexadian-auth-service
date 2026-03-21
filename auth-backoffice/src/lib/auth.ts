import {
  createLocalStorage,
  extractUserContext,
  hasAnyPermission as hasAnyPermissionCore,
  isTokenExpired,
  type TokenStorage,
  type UserContext,
  type TokenResponse,
} from "@hexadian-corporation/auth-core";
import { refreshToken as refreshTokenApi } from "@/api/auth";

export type { UserContext, TokenResponse };

const PORTAL_URL = import.meta.env.VITE_AUTH_PORTAL_URL ?? "http://localhost:3003";

// Use empty prefix for backward compatibility with existing localStorage keys
const storage: TokenStorage = createLocalStorage("");

export function storeTokens(tokens: TokenResponse): void {
  storage.storeTokens(tokens.access_token, tokens.refresh_token);
}

export function getAccessToken(): string | null {
  return storage.getAccessToken();
}

export function getRefreshToken(): string | null {
  return storage.getRefreshToken();
}

export function clearTokens(): void {
  storage.clearTokens();
}

export function parseAccessToken(): UserContext | null {
  const token = getAccessToken();
  if (!token) return null;
  return extractUserContext(token);
}

export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;
  return !isTokenExpired(token);
}

export function getUserContext(): UserContext | null {
  return parseAccessToken();
}

export function hasAnyPermission(required: string[]): boolean {
  const user = parseAccessToken();
  if (!user) return false;
  return hasAnyPermissionCore(user, required);
}

export function redirectToPortal(returnPath = "/"): void {
  const redirectUri = `${window.location.origin}/callback`;
  const state = encodeURIComponent(returnPath);
  window.location.href = `${PORTAL_URL}/login?redirect_uri=${encodeURIComponent(redirectUri)}&state=${state}`;
}

export async function authFetch(
  input: string | URL | Request,
  init?: RequestInit,
): Promise<Response> {
  const accessToken = getAccessToken();
  const headers = new Headers(init?.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let res = await fetch(input, { ...init, headers });

  if (res.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      res = await fetch(input, { ...init, headers });
    }
  }

  return res;
}

async function tryRefreshToken(): Promise<string | null> {
  const token = getRefreshToken();
  if (!token) return null;

  try {
    const tokens = await refreshTokenApi(token);
    storeTokens(tokens);
    return tokens.access_token;
  } catch {
    clearTokens();
    return null;
  }
}
