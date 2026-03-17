import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RegisterPage from "@/pages/RegisterPage";
import type { User } from "@/types/auth";

vi.mock("@/api/auth", () => ({
  register: vi.fn(),
  login: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  storeTokens: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { register, login } from "@/api/auth";
import { storeTokens } from "@/lib/auth";
const mockRegister = vi.mocked(register);
const mockLogin = vi.mocked(login);
const mockStoreTokens = vi.mocked(storeTokens);

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
}

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the create account heading", () => {
    renderPage();
    expect(
      screen.getByRole("heading", { name: "Create Account" }),
    ).toBeInTheDocument();
  });

  it("renders all form fields", () => {
    renderPage();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm Password")).toBeInTheDocument();
    expect(screen.getByLabelText("RSI Handle")).toBeInTheDocument();
  });

  it("renders submit button", () => {
    renderPage();
    expect(
      screen.getByRole("button", { name: "Create Account" }),
    ).toBeInTheDocument();
  });

  it("renders link to login page", () => {
    renderPage();
    const link = screen.getByRole("link", { name: "Log in" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/login");
  });

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(screen.getByText("Username is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
    expect(
      screen.getByText("Please confirm your password"),
    ).toBeInTheDocument();
    expect(screen.getByText("RSI handle is required")).toBeInTheDocument();
  });

  it("shows password mismatch error", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "different");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
  });

  it("shows password too short error", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.type(screen.getByLabelText("Confirm Password"), "short");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(
      screen.getByText("Password must be at least 8 characters"),
    ).toBeInTheDocument();
  });

  it("shows RSI handle format error", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "password123");
    await user.type(screen.getByLabelText("RSI Handle"), "a@");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(
      screen.getByText(
        "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
      ),
    ).toBeInTheDocument();
  });

  it("calls register API and navigates on success", async () => {
    mockRegister.mockResolvedValueOnce({
      _id: "123",
      username: "testuser",
      roles: ["user"],
      is_active: true,
      rsi_handle: "test-handle",
      rsi_verified: false,
    });
    mockLogin.mockResolvedValueOnce({
      access_token: "test-access",
      refresh_token: "test-refresh",
      token_type: "bearer",
      expires_in: 900,
    });

    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "password123");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        username: "testuser",
        password: "password123",
        rsi_handle: "test-handle",
      });
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: "testuser",
        password: "password123",
      });
    });

    expect(mockStoreTokens).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/verify?");
  });

  it("displays API error on failure", async () => {
    mockRegister.mockRejectedValueOnce(
      new Error("Username/RSI handle already taken"),
    );

    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "password123");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(
        screen.getByText("Username/RSI handle already taken"),
      ).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("does not call API when validation fails", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Create Account" }));

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it("disables submit button while submitting", async () => {
    let resolveRegister!: (value: User) => void;
    mockRegister.mockImplementationOnce(
      () =>
        new Promise<User>((resolve) => {
          resolveRegister = resolve;
        }),
    );

    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "password123");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Creating Account…" }),
      ).toBeDisabled();
    });

    resolveRegister!({
      _id: "123",
      username: "testuser",
      roles: ["user"],
      is_active: true,
      rsi_handle: "test-handle",
      rsi_verified: false,
    });
  });

  it("handles non-Error rejection", async () => {
    mockRegister.mockRejectedValueOnce("unexpected");

    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "testuser");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.type(screen.getByLabelText("Confirm Password"), "password123");
    await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(screen.getByText("Registration failed")).toBeInTheDocument();
    });
  });
});
