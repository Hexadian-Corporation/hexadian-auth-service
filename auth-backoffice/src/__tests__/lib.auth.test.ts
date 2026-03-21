import { describe, it, expect, vi, beforeEach } from "vitest";
import type { UserContext, TokenResponse } from "@hexadian-corporation/auth-core";

const mockStorage = vi.hoisted(() => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  storeTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

vi.mock("@hexadian-corporation/auth-core", () => ({
  createLocalStorage: vi.fn(() => mockStorage),
  extractUserContext: vi.fn(),
  hasAnyPermission: vi.fn(),
  isTokenExpired: vi.fn(),
}));

vi.mock("@/api/auth", () => ({
  refreshToken: vi.fn(),
}));

import {
  createLocalStorage,
  extractUserContext,
  hasAnyPermission as hasAnyPermissionCore,
  isTokenExpired,
} from "@hexadian-corporation/auth-core";
import { refreshToken as refreshTokenApi } from "@/api/auth";
import {
  storeTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  parseAccessToken,
  isAuthenticated,
  getUserContext,
  hasAnyPermission,
  redirectToPortal,
  authFetch,
} from "@/lib/auth";

const mockUser: UserContext = {
  userId: "u1",
  username: "admin",
  groups: ["admins"],
  roles: ["auth-admin"],
  permissions: ["auth:users:read", "auth:rbac:manage"],
  rsiHandle: "AdminRSI",
  rsiVerified: true,
};

const mockTokens: TokenResponse = {
  access_token: "new-access",
  refresh_token: "new-refresh",
  token_type: "bearer",
  expires_in: 900,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("module initialization", () => {
  it("initializes storage with empty prefix for backward compatibility", async () => {
    vi.resetModules();
    await import("@/lib/auth");
    expect(createLocalStorage).toHaveBeenCalledWith("");
  });
});

describe("storeTokens", () => {
  it("delegates to storage.storeTokens", () => {
    storeTokens(mockTokens);
    expect(mockStorage.storeTokens).toHaveBeenCalledWith("new-access", "new-refresh");
  });
});

describe("getAccessToken", () => {
  it("returns token from storage", () => {
    mockStorage.getAccessToken.mockReturnValue("tok");
    expect(getAccessToken()).toBe("tok");
  });
});

describe("getRefreshToken", () => {
  it("returns refresh token from storage", () => {
    mockStorage.getRefreshToken.mockReturnValue("ref-tok");
    expect(getRefreshToken()).toBe("ref-tok");
  });
});

describe("clearTokens", () => {
  it("delegates to storage.clearTokens", () => {
    clearTokens();
    expect(mockStorage.clearTokens).toHaveBeenCalled();
  });
});

describe("parseAccessToken", () => {
  it("returns null when no token", () => {
    mockStorage.getAccessToken.mockReturnValue(null);
    expect(parseAccessToken()).toBeNull();
  });

  it("returns user context when token exists", () => {
    mockStorage.getAccessToken.mockReturnValue("valid-token");
    vi.mocked(extractUserContext).mockReturnValue(mockUser);
    expect(parseAccessToken()).toEqual(mockUser);
    expect(extractUserContext).toHaveBeenCalledWith("valid-token");
  });
});

describe("isAuthenticated", () => {
  it("returns false when no token", () => {
    mockStorage.getAccessToken.mockReturnValue(null);
    expect(isAuthenticated()).toBe(false);
  });

  it("returns true when token is not expired", () => {
    mockStorage.getAccessToken.mockReturnValue("valid-token");
    vi.mocked(isTokenExpired).mockReturnValue(false);
    expect(isAuthenticated()).toBe(true);
  });

  it("returns false when token is expired", () => {
    mockStorage.getAccessToken.mockReturnValue("expired-token");
    vi.mocked(isTokenExpired).mockReturnValue(true);
    expect(isAuthenticated()).toBe(false);
  });
});

describe("getUserContext", () => {
  it("returns parsed user context", () => {
    mockStorage.getAccessToken.mockReturnValue("token");
    vi.mocked(extractUserContext).mockReturnValue(mockUser);
    expect(getUserContext()).toEqual(mockUser);
  });
});

describe("hasAnyPermission", () => {
  it("returns false when no user", () => {
    mockStorage.getAccessToken.mockReturnValue(null);
    expect(hasAnyPermission(["auth:users:read"])).toBe(false);
  });

  it("delegates to auth-core when user exists", () => {
    mockStorage.getAccessToken.mockReturnValue("token");
    vi.mocked(extractUserContext).mockReturnValue(mockUser);
    vi.mocked(hasAnyPermissionCore).mockReturnValue(true);
    expect(hasAnyPermission(["auth:users:read"])).toBe(true);
    expect(hasAnyPermissionCore).toHaveBeenCalledWith(mockUser, ["auth:users:read"]);
  });
});

describe("redirectToPortal", () => {
  it("redirects to portal login URL with return path", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "", origin: "http://localhost:3002" },
    });
    redirectToPortal("/dashboard");
    expect(window.location.href).toContain("login");
    expect(window.location.href).toContain("redirect_uri");
    expect(window.location.href).toContain(encodeURIComponent("/dashboard"));
  });

  it("uses / as default return path", () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "", origin: "http://localhost:3002" },
    });
    redirectToPortal();
    expect(window.location.href).toContain(encodeURIComponent("/"));
  });
});

describe("authFetch", () => {
  it("adds Authorization header when token exists", async () => {
    mockStorage.getAccessToken.mockReturnValue("access-token");
    const mockResponse = { ok: true, status: 200 } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

    const res = await authFetch("http://api/data");
    expect(res).toBe(mockResponse);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("makes request without auth header when no token", async () => {
    mockStorage.getAccessToken.mockReturnValue(null);
    const mockResponse = { ok: true, status: 200 } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

    const res = await authFetch("http://api/data");
    expect(res).toBe(mockResponse);
  });

  it("retries with refreshed token on 401", async () => {
    mockStorage.getAccessToken.mockReturnValue("old-token");
    mockStorage.getRefreshToken.mockReturnValue("refresh-token");
    vi.mocked(refreshTokenApi).mockResolvedValue(mockTokens);

    const unauthorizedResponse = { ok: false, status: 401 } as Response;
    const okResponse = { ok: true, status: 200 } as Response;
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(unauthorizedResponse)
        .mockResolvedValueOnce(okResponse),
    );

    const res = await authFetch("http://api/protected");
    expect(res).toBe(okResponse);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(refreshTokenApi).toHaveBeenCalledWith("refresh-token");
  });

  it("clears tokens and returns 401 when refresh fails", async () => {
    mockStorage.getAccessToken.mockReturnValue("old-token");
    mockStorage.getRefreshToken.mockReturnValue("bad-refresh");
    vi.mocked(refreshTokenApi).mockRejectedValue(new Error("Refresh failed"));

    const unauthorizedResponse = { ok: false, status: 401 } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(unauthorizedResponse));

    const res = await authFetch("http://api/protected");
    expect(res).toBe(unauthorizedResponse);
    expect(mockStorage.clearTokens).toHaveBeenCalled();
  });

  it("returns non-401 errors without retry", async () => {
    mockStorage.getAccessToken.mockReturnValue("token");
    const serverError = { ok: false, status: 500 } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(serverError));

    const res = await authFetch("http://api/data");
    expect(res).toBe(serverError);
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
