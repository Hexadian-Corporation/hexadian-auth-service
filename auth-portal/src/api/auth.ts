import type {
  RegisterRequest,
  LoginRequest,
  AuthorizeRequest,
  AuthorizeResponse,
  TokenExchangeRequest,
  TokenResponse,
  User,
  VerificationStartRequest,
  VerificationStartResponse,
  VerificationConfirmRequest,
  ChangePasswordRequest,
} from "@/types/auth";

const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL ?? "http://localhost:8006";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${AUTH_API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(
      (body as { detail?: string } | null)?.detail ?? `Request failed: ${res.status}`,
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function register(data: RegisterRequest): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function login(data: LoginRequest): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function authorize(data: AuthorizeRequest): Promise<AuthorizeResponse> {
  return request<AuthorizeResponse>("/auth/authorize", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function exchangeCode(
  data: TokenExchangeRequest,
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/token/exchange", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function refreshToken(token: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/token/refresh", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function revokeToken(token: string): Promise<void> {
  return request<void>("/auth/token/revoke", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function startVerification(
  data: VerificationStartRequest,
  token: string,
): Promise<VerificationStartResponse> {
  return request<VerificationStartResponse>("/auth/verify/start", {
    method: "POST",
    body: JSON.stringify(data),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function confirmVerification(
  data: VerificationConfirmRequest,
  token: string,
): Promise<VerificationStartResponse> {
  return request<VerificationStartResponse>("/auth/verify/confirm", {
    method: "POST",
    body: JSON.stringify(data),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function changePassword(
  data: ChangePasswordRequest,
  token: string,
): Promise<void> {
  return request<void>("/auth/password/change", {
    method: "POST",
    body: JSON.stringify(data),
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getUser(userId: string, token: string): Promise<User> {
  return request<User>(`/auth/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
