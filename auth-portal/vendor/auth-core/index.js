// @hexadian-corporation/auth-core — vendored build
// Source: https://github.com/Hexadian-Corporation/hexadian-auth-client/tree/main/packages/core

// ── types.ts ──────────────────────────────────────────────────────────────────
// (interfaces only — no runtime output)

// ── storage.ts ────────────────────────────────────────────────────────────────

/**
 * Create a {@link TokenStorage} backed by `localStorage`.
 *
 * @param prefix - Key prefix used for localStorage entries.
 *   Defaults to `"hexadian_auth_"`.
 *   Keys stored: `{prefix}access_token`, `{prefix}refresh_token`.
 */
export function createLocalStorage(prefix = 'hexadian_auth_') {
  const accessKey = `${prefix}access_token`;
  const refreshKey = `${prefix}refresh_token`;

  return {
    getAccessToken() {
      return localStorage.getItem(accessKey);
    },
    getRefreshToken() {
      return localStorage.getItem(refreshKey);
    },
    storeTokens(accessToken, refreshToken) {
      localStorage.setItem(accessKey, accessToken);
      localStorage.setItem(refreshKey, refreshToken);
    },
    clearTokens() {
      localStorage.removeItem(accessKey);
      localStorage.removeItem(refreshKey);
    },
  };
}

// ── jwt.ts ────────────────────────────────────────────────────────────────────

/**
 * Decode a JWT payload section (the second dot-delimited segment).
 * Handles base64url encoding with or without padding.
 *
 * @returns The parsed payload as a record, or `null` if the token is malformed.
 */
export function decodeJwtPayload(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      '=',
    );

    const json = atob(padded);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

/**
 * Check whether a JWT token is expired.
 *
 * @returns `true` if the token is expired or cannot be decoded, `false` otherwise.
 */
export function isTokenExpired(token) {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return true;
  return payload.exp * 1000 <= Date.now();
}

/**
 * Extract a {@link UserContext} from a JWT access token.
 *
 * @returns The extracted context, or `null` if the token is invalid or expired.
 */
export function extractUserContext(token) {
  const payload = decodeJwtPayload(token);
  if (!payload) return null;

  if (typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now()) {
    return null;
  }

  if (typeof payload.sub !== 'string' || typeof payload.username !== 'string') {
    return null;
  }

  return {
    userId: payload.sub,
    username: payload.username,
    groups: asStringArray(payload.groups),
    roles: asStringArray(payload.roles),
    permissions: asStringArray(payload.permissions),
    rsiHandle: typeof payload.rsi_handle === 'string' ? payload.rsi_handle : null,
    rsiVerified: payload.rsi_verified === true,
  };
}

function asStringArray(value) {
  return Array.isArray(value) ? value.filter((v) => typeof v === 'string') : [];
}

// ── permissions.ts ────────────────────────────────────────────────────────────

/**
 * Check whether a user has **all** of the specified permissions.
 */
export function hasAllPermissions(user, required) {
  return required.every((p) => user.permissions.includes(p));
}

/**
 * Check whether a user has **at least one** of the specified permissions.
 */
export function hasAnyPermission(user, required) {
  return required.some((p) => user.permissions.includes(p));
}

// ── oauth-state.ts ────────────────────────────────────────────────────────────

const OAUTH_STATE_KEY = 'hexadian_auth_oauth_state';

export function generateOAuthState() {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  const state = Array.from(array)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  sessionStorage.setItem(OAUTH_STATE_KEY, state);
  return state;
}

export function verifyOAuthState(state) {
  const stored = sessionStorage.getItem(OAUTH_STATE_KEY);
  sessionStorage.removeItem(OAUTH_STATE_KEY);
  return stored !== null && stored === state;
}

export function clearOAuthState() {
  sessionStorage.removeItem(OAUTH_STATE_KEY);
}

// ── api.ts ────────────────────────────────────────────────────────────────────

export class AuthApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'AuthApiError';
    this.status = status;
  }
}

export function createAuthApiClient(baseUrl) {
  const base = baseUrl.replace(/\/+$/, '');

  async function post(path, body) {
    const response = await fetch(`${base}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let message = response.statusText;
      try {
        const json = await response.json();
        message = json.detail ?? json.message ?? message;
      } catch {
        // ignore
      }
      throw new AuthApiError(response.status, message);
    }

    return response.json();
  }

  function toTokenPair(raw) {
    return { accessToken: raw.access_token, refreshToken: raw.refresh_token };
  }

  return {
    async exchangeCode(code, redirectUri) {
      const raw = await post('/auth/token/exchange', { code, redirect_uri: redirectUri });
      return toTokenPair(raw);
    },
    async refreshToken(refreshToken) {
      const raw = await post('/auth/token/refresh', { refresh_token: refreshToken });
      return toTokenPair(raw);
    },
    async revokeToken(refreshToken) {
      await post('/auth/token/revoke', { refresh_token: refreshToken });
    },
  };
}

// ── authenticated-fetch.ts ────────────────────────────────────────────────────

export function createAuthenticatedFetch(options) {
  const { tokenStorage, authApiClient, onAuthFailure } = options;

  let refreshPromise = null;

  async function doRefresh() {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) {
      tokenStorage.clearTokens();
      onAuthFailure?.();
      throw new Error('No refresh token available');
    }
    try {
      const tokenPair = await authApiClient.refreshToken(refreshToken);
      tokenStorage.storeTokens(tokenPair.accessToken, tokenPair.refreshToken);
    } catch (err) {
      tokenStorage.clearTokens();
      onAuthFailure?.();
      throw err;
    }
  }

  function ensureRefreshed() {
    if (!refreshPromise) {
      refreshPromise = doRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  }

  function buildHeaders(initHeaders, token) {
    const headers = new Headers(initHeaders);
    if (token !== null) {
      headers.set('Authorization', 'Bearer ' + token);
    }
    return headers;
  }

  return async function authenticatedFetch(input, init) {
    const currentToken = tokenStorage.getAccessToken();
    if (currentToken !== null && isTokenExpired(currentToken)) {
      await ensureRefreshed();
    }

    const accessToken = tokenStorage.getAccessToken();
    const response = await fetch(input, {
      ...init,
      headers: buildHeaders(init?.headers, accessToken),
    });

    if (response.status === 401) {
      try {
        await ensureRefreshed();
      } catch {
        return response;
      }

      const newToken = tokenStorage.getAccessToken();
      return fetch(input, {
        ...init,
        headers: buildHeaders(init?.headers, newToken),
      });
    }

    return response;
  };
}

// ── redirect.ts ───────────────────────────────────────────────────────────────

export function buildLoginUrl(options) {
  const { portalUrl, redirectUri, state } = options;
  const oauthState = state ?? generateOAuthState();
  const base = portalUrl.replace(/\/+$/, '');
  const url = new URL(`${base}/login`);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('state', oauthState);
  return url.toString();
}

export function redirectToLogin(options) {
  window.location.href = buildLoginUrl(options);
}
