import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  storeTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  authFetch,
} from "@/lib/auth";

vi.mock("@/api/auth", () => ({
  refreshToken: vi.fn(),
}));

import { refreshToken } from "@/api/auth";
const mockRefreshToken = vi.mocked(refreshToken);

describe("token storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("stores and retrieves tokens", () => {
    storeTokens({
      access_token: "access-123",
      refresh_token: "refresh-456",
      token_type: "bearer",
      expires_in: 3600,
    });

    expect(getAccessToken()).toBe("access-123");
    expect(getRefreshToken()).toBe("refresh-456");
  });

  it("returns null when no tokens stored", () => {
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("clears tokens", () => {
    storeTokens({
      access_token: "access-123",
      refresh_token: "refresh-456",
      token_type: "bearer",
      expires_in: 3600,
    });

    clearTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});

describe("authFetch", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it("attaches Authorization header when token exists", async () => {
    storeTokens({
      access_token: "my-token",
      refresh_token: "refresh",
      token_type: "bearer",
      expires_in: 3600,
    });

    const mockFetch = vi.fn().mockResolvedValue({ status: 200 });
    vi.stubGlobal("fetch", mockFetch);

    await authFetch("http://api.test/data");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer my-token");
  });

  it("does not attach header when no token", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ status: 200 });
    vi.stubGlobal("fetch", mockFetch);

    await authFetch("http://api.test/data");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.has("Authorization")).toBe(false);
  });

  it("retries with refreshed token on 401", async () => {
    storeTokens({
      access_token: "old-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      expires_in: 3600,
    });

    mockRefreshToken.mockResolvedValueOnce({
      access_token: "new-token",
      refresh_token: "new-refresh",
      token_type: "bearer",
      expires_in: 3600,
    });

    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({ status: 401 })
      .mockResolvedValueOnce({ status: 200 });
    vi.stubGlobal("fetch", mockFetch);

    const res = await authFetch("http://api.test/data");

    expect(mockRefreshToken).toHaveBeenCalledWith("refresh-token");
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(res.status).toBe(200);

    const [, retryInit] = mockFetch.mock.calls[1] as [string, RequestInit];
    const headers = retryInit.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer new-token");
  });

  it("clears tokens when refresh fails", async () => {
    storeTokens({
      access_token: "old-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      expires_in: 3600,
    });

    mockRefreshToken.mockRejectedValueOnce(new Error("expired"));

    const mockFetch = vi.fn().mockResolvedValue({ status: 401 });
    vi.stubGlobal("fetch", mockFetch);

    await authFetch("http://api.test/data");

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("returns 401 response when no refresh token", async () => {
    storeTokens({
      access_token: "old-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      expires_in: 3600,
    });
    localStorage.removeItem("refresh_token");

    const mockFetch = vi.fn().mockResolvedValue({ status: 401 });
    vi.stubGlobal("fetch", mockFetch);

    const res = await authFetch("http://api.test/data");

    expect(res.status).toBe(401);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});
