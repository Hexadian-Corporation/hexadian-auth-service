import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import CallbackPage from "@/pages/CallbackPage";
import type { TokenResponse } from "@/types/auth";

vi.mock("@/api/auth", () => ({
  exchangeCode: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  storeTokens: vi.fn(),
}));

import { exchangeCode } from "@/api/auth";
import { storeTokens } from "@/lib/auth";
const mockExchangeCode = vi.mocked(exchangeCode);
const mockStoreTokens = vi.mocked(storeTokens);

function renderPage(initialEntries: string[] = ["/callback"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <CallbackPage />
    </MemoryRouter>,
  );
}

describe("CallbackPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "http://localhost:3003/callback", origin: "http://localhost:3003" },
    });
  });

  it("shows error when no code param is present", () => {
    renderPage();
    expect(screen.getByText("Missing authorization code")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows processing state when code is present", () => {
    mockExchangeCode.mockReturnValue(new Promise(() => {}));
    renderPage(["/callback?code=abc123&state=xyz"]);
    expect(screen.getByText("Processing...")).toBeInTheDocument();
  });

  it("exchanges code for tokens and stores them", async () => {
    const tokens: TokenResponse = {
      access_token: "access-123",
      refresh_token: "refresh-456",
      token_type: "bearer",
      expires_in: 3600,
    };
    mockExchangeCode.mockResolvedValueOnce(tokens);

    renderPage(["/callback?code=abc123&state=xyz"]);

    await waitFor(() => {
      expect(mockExchangeCode).toHaveBeenCalledWith({
        code: "abc123",
        redirect_uri: "http://localhost:3003/callback",
      });
    });

    await waitFor(() => {
      expect(mockStoreTokens).toHaveBeenCalledWith(tokens);
    });
  });

  it("shows error on exchange failure", async () => {
    mockExchangeCode.mockRejectedValueOnce(new Error("Invalid code"));

    renderPage(["/callback?code=bad-code"]);

    await waitFor(() => {
      expect(screen.getByText("Invalid code")).toBeInTheDocument();
    });
  });

  it("handles non-Error rejection", async () => {
    mockExchangeCode.mockRejectedValueOnce("unexpected");

    renderPage(["/callback?code=bad-code"]);

    await waitFor(() => {
      expect(screen.getByText("Token exchange failed")).toBeInTheDocument();
    });
  });
});
