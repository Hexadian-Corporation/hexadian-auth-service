// @hexadian-corporation/auth-core — vendored type declarations

// ── types ─────────────────────────────────────────────────────────────────────

/**
 * Decoded user identity from a JWT access token.
 * Must align with JWT claims from hexadian-auth-service.
 */
export interface UserContext {
  userId: string;
  username: string;
  groups: string[];
  roles: string[];
  permissions: string[];
  rsiHandle: string | null;
  rsiVerified: boolean;
}

/** Access + refresh token pair returned by the auth service. */
export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

/** Full token response from the auth service token endpoint. */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/** Configuration for the auth client SDK. */
export interface AuthConfig {
  authServiceUrl: string;
  clientId: string;
  redirectUri: string;
  storagePrefix?: string;
  autoRefresh?: boolean;
}

// ── storage ───────────────────────────────────────────────────────────────────

export interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  storeTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
}

export function createLocalStorage(prefix?: string): TokenStorage;

// ── jwt ───────────────────────────────────────────────────────────────────────

export function decodeJwtPayload(token: string): Record<string, unknown> | null;
export function isTokenExpired(token: string): boolean;
export function extractUserContext(token: string): UserContext | null;

// ── permissions ───────────────────────────────────────────────────────────────

export function hasAllPermissions(user: UserContext, required: string[]): boolean;
export function hasAnyPermission(user: UserContext, required: string[]): boolean;

// ── oauth-state ───────────────────────────────────────────────────────────────

export function generateOAuthState(): string;
export function verifyOAuthState(state: string): boolean;
export function clearOAuthState(): void;

// ── api ───────────────────────────────────────────────────────────────────────

export class AuthApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string);
}

export interface AuthApiClient {
  exchangeCode(code: string, redirectUri: string): Promise<TokenPair>;
  refreshToken(refreshToken: string): Promise<TokenPair>;
  revokeToken(refreshToken: string): Promise<void>;
}

export function createAuthApiClient(baseUrl: string): AuthApiClient;

// ── authenticated-fetch ───────────────────────────────────────────────────────

export interface AuthenticatedFetchOptions {
  tokenStorage: TokenStorage;
  authApiClient: AuthApiClient;
  onAuthFailure?: () => void;
}

export function createAuthenticatedFetch(options: AuthenticatedFetchOptions): typeof fetch;

// ── redirect ──────────────────────────────────────────────────────────────────

export interface LoginUrlOptions {
  portalUrl: string;
  redirectUri: string;
  state?: string;
}

export function buildLoginUrl(options: LoginUrlOptions): string;
export function redirectToLogin(options: LoginUrlOptions): void;
