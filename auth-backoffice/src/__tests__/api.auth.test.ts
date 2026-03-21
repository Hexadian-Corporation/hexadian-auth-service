import { describe, it, expect, vi, beforeEach } from "vitest";
import { exchangeCode, login, refreshToken } from "@/api/auth";
import type { TokenResponse } from "@/lib/auth";

const mockTokenResponse: TokenResponse = {
  access_token: "mock-access-token",
  refresh_token: "mock-refresh-token",
  token_type: "bearer",
  expires_in: 900,
};

function mockFetch(ok: boolean, body: unknown, status = ok ? 200 : 400, statusText = ok ? "OK" : "Bad Request") {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok,
    status,
    statusText,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response));
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("exchangeCode", () => {
  it("returns token response on success", async () => {
    mockFetch(true, mockTokenResponse);
    const result = await exchangeCode("auth-code", "http://localhost:3002/callback");
    expect(result).toEqual(mockTokenResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/token/exchange"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws on error response", async () => {
    mockFetch(false, null, 400, "Bad Request");
    await expect(exchangeCode("bad-code", "http://localhost:3002/callback")).rejects.toThrow(
      "Token exchange failed",
    );
  });
});

describe("login", () => {
  it("returns token response on success", async () => {
    mockFetch(true, mockTokenResponse);
    const result = await login({ username: "admin", password: "password" });
    expect(result).toEqual(mockTokenResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/login"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws on error response", async () => {
    mockFetch(false, null, 401, "Unauthorized");
    await expect(login({ username: "admin", password: "wrong" })).rejects.toThrow("Login failed");
  });
});

describe("refreshToken", () => {
  it("returns token response on success", async () => {
    mockFetch(true, mockTokenResponse);
    const result = await refreshToken("mock-refresh-token");
    expect(result).toEqual(mockTokenResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/token/refresh"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws on error response", async () => {
    mockFetch(false, null, 401, "Unauthorized");
    await expect(refreshToken("expired-token")).rejects.toThrow("Token refresh failed");
  });
});
