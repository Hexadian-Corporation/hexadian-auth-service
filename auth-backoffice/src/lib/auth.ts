interface UserContext {
  userId: string;
  username: string;
  groups: string[];
  roles: string[];
  permissions: string[];
  rsiHandle: string | null;
  rsiVerified: boolean;
}

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

const PORTAL_URL = import.meta.env.VITE_AUTH_PORTAL_URL ?? "http://localhost:3003";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split(".")[1])) as { exp: number };
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getUserContext(): UserContext | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return {
      userId: payload.sub ?? payload.user_id ?? "",
      username: payload.username ?? "",
      groups: payload.groups ?? [],
      roles: payload.roles ?? [],
      permissions: payload.permissions ?? [],
      rsiHandle: payload.rsi_handle ?? null,
      rsiVerified: payload.rsi_verified ?? false,
    };
  } catch {
    return null;
  }
}

export function hasAnyPermission(required: string[]): boolean {
  const ctx = getUserContext();
  if (!ctx) return false;
  return required.some((p) => ctx.permissions.includes(p));
}

export function storeTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function redirectToPortal(returnPath = "/"): void {
  const redirectUri = `${window.location.origin}/callback`;
  const state = encodeURIComponent(returnPath);
  window.location.href = `${PORTAL_URL}/login?redirect_uri=${encodeURIComponent(redirectUri)}&state=${state}`;
}

export function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}
