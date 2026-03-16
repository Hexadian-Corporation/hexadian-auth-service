import type { TokenResponse } from "@/types/auth";
import { refreshToken as refreshTokenApi } from "@/api/auth";

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export interface AccessTokenPayload {
  sub: string;
  username: string;
  rsi_handle: string | null;
  rsi_verified: boolean;
}

export function parseAccessToken(): AccessTokenPayload | null {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1])) as Record<string, unknown>;
    return {
      sub: payload.sub as string,
      username: payload.username as string,
      rsi_handle: (payload.rsi_handle as string | undefined) ?? null,
      rsi_verified: (payload.rsi_verified as boolean | undefined) ?? false,
    };
  } catch {
    return null;
  }
}

export function storeTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
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
