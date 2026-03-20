import {
  createLocalStorage,
  extractUserContext,
  type TokenStorage,
  type UserContext,
  type TokenResponse,
} from "@hexadian-corporation/auth-core";
import { refreshToken as refreshTokenApi } from "@/api/auth";

export type { UserContext, TokenResponse };

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
