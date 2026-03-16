import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, it, expect } from "vitest";
import AppRouter from "@/router";

describe("AppRouter", () => {
  it("renders without crashing", () => {
    render(<AppRouter />);
  });
});

describe("LoginPage", () => {
  it("renders the sign in heading", async () => {
    const { default: LoginPage } = await import("@/pages/LoginPage");
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("heading", { name: "Sign In" }),
    ).toBeInTheDocument();
  });
});

describe("RegisterPage", () => {
  it("renders the create account heading", async () => {
    const { default: RegisterPage } = await import("@/pages/RegisterPage");
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("heading", { name: "Create Account" }),
    ).toBeInTheDocument();
  });
});

describe("VerifyPage", () => {
  it("renders the RSI verification heading", async () => {
    const { default: VerifyPage } = await import("@/pages/VerifyPage");
    render(
      <MemoryRouter>
        <VerifyPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("RSI Verification")).toBeInTheDocument();
  });
});

describe("ChangePasswordPage", () => {
  it("renders the change password heading", async () => {
    const { default: ChangePasswordPage } = await import(
      "@/pages/ChangePasswordPage"
    );
    render(
      <MemoryRouter>
        <ChangePasswordPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("Change Password")).toBeInTheDocument();
  });
});

describe("CallbackPage", () => {
  it("renders error when no code param", async () => {
    const { default: CallbackPage } = await import("@/pages/CallbackPage");
    render(
      <MemoryRouter>
        <CallbackPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("Missing authorization code")).toBeInTheDocument();
  });
});
