import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import LoginPage from "@/pages/LoginPage";
import type { AuthorizeResponse, TokenResponse } from "@/types/auth";

vi.mock("@/api/auth", () => ({
  login: vi.fn(),
  authorize: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  storeTokens: vi.fn(),
}));

import { login, authorize } from "@/api/auth";
import { storeTokens } from "@/lib/auth";
const mockLogin = vi.mocked(login);
const mockAuthorize = vi.mocked(authorize);
const mockStoreTokens = vi.mocked(storeTokens);

function renderPage(initialEntries: string[] = ["/login"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <LoginPage />
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.location mock
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "http://localhost:3003/login", search: "" },
    });
  });

  it("renders the sign in heading", () => {
    renderPage();
    expect(
      screen.getByRole("heading", { name: "Sign In" }),
    ).toBeInTheDocument();
  });

  it("renders username and password fields", () => {
    renderPage();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("renders submit button", () => {
    renderPage();
    expect(
      screen.getByRole("button", { name: "Sign In" }),
    ).toBeInTheDocument();
  });

  it("renders link to register page", () => {
    renderPage();
    const link = screen.getByRole("link", { name: "Register" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/register");
  });

  it("renders forgot password link", () => {
    renderPage();
    const link = screen.getByRole("link", { name: "Forgot your password?" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/password/forgot");
  });

  it("preserves redirect_uri in forgot password link", () => {
    renderPage([
      "/login?redirect_uri=http://localhost:3000/callback&state=xyz",
    ]);
    const link = screen.getByRole("link", { name: "Forgot your password?" });
    expect(link).toHaveAttribute(
      "href",
      "/password/forgot?redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback&state=xyz",
    );
  });

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(screen.getByText("Username is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
  });

  it("does not call API when validation fails", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(mockLogin).not.toHaveBeenCalled();
    expect(mockAuthorize).not.toHaveBeenCalled();
  });

  describe("direct login (no redirect_uri)", () => {
    it("calls login API and stores tokens on success", async () => {
      const tokens: TokenResponse = {
        access_token: "access-123",
        refresh_token: "refresh-456",
        token_type: "bearer",
        expires_in: 3600,
      };
      mockLogin.mockResolvedValueOnce(tokens);

      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "password123");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: "testuser",
          password: "password123",
        });
      });

      expect(mockStoreTokens).toHaveBeenCalledWith(tokens);
      expect(window.location.href).toBe("/");
    });

    it("displays API error on login failure", async () => {
      mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"));

      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "wrongpass");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
      });
    });

    it("handles non-Error rejection", async () => {
      mockLogin.mockRejectedValueOnce("unexpected");

      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "password123");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(screen.getByText("Login failed")).toBeInTheDocument();
      });
    });
  });

  describe("redirect flow (with redirect_uri)", () => {
    it("calls authorize API and redirects with code", async () => {
      const response: AuthorizeResponse = {
        code: "auth-code-123",
        state: "xyz",
        redirect_uri: "http://localhost:3000/callback",
      };
      mockAuthorize.mockResolvedValueOnce(response);

      const user = userEvent.setup();
      renderPage([
        "/login?redirect_uri=http://localhost:3000/callback&state=xyz",
      ]);

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "password123");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(mockAuthorize).toHaveBeenCalledWith({
          username: "testuser",
          password: "password123",
          redirect_uri: "http://localhost:3000/callback",
          state: "xyz",
        });
      });

      expect(mockLogin).not.toHaveBeenCalled();
      expect(mockStoreTokens).not.toHaveBeenCalled();
      expect(window.location.href).toBe(
        "http://localhost:3000/callback?code=auth-code-123&state=xyz",
      );
    });

    it("displays API error on authorize failure", async () => {
      mockAuthorize.mockRejectedValueOnce(
        new Error("Invalid credentials"),
      );

      const user = userEvent.setup();
      renderPage([
        "/login?redirect_uri=http://localhost:3000/callback&state=xyz",
      ]);

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "wrongpass");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
      });
    });

    it("defaults state to empty string when not provided", async () => {
      const response: AuthorizeResponse = {
        code: "auth-code-123",
        state: "",
        redirect_uri: "http://localhost:3000/callback",
      };
      mockAuthorize.mockResolvedValueOnce(response);

      const user = userEvent.setup();
      renderPage(["/login?redirect_uri=http://localhost:3000/callback"]);

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("Password"), "password123");
      await user.click(screen.getByRole("button", { name: "Sign In" }));

      await waitFor(() => {
        expect(mockAuthorize).toHaveBeenCalledWith({
          username: "testuser",
          password: "password123",
          redirect_uri: "http://localhost:3000/callback",
          state: "",
        });
      });
    });
  });

  it("disables submit button while submitting", async () => {
    let resolveLogin!: (value: TokenResponse) => void;
    mockLogin.mockImplementationOnce(
      () =>
        new Promise<TokenResponse>((resolve) => {
          resolveLogin = resolve;
        }),
    );

    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Signing In…" }),
      ).toBeDisabled();
    });

    resolveLogin!({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 3600,
    });
  });
});
