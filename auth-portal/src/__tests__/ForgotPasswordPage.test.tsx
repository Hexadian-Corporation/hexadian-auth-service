import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage";
import type { ForgotPasswordResponse } from "@/types/auth";

vi.mock("@/api/auth", () => ({
  forgotPassword: vi.fn(),
  confirmForgotPassword: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { forgotPassword, confirmForgotPassword } from "@/api/auth";
const mockForgotPassword = vi.mocked(forgotPassword);
const mockConfirmForgotPassword = vi.mocked(confirmForgotPassword);

function renderPage(initialEntries: string[] = ["/password/forgot"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );
}

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("Step 1 — Identity", () => {
    it("renders the forgot password heading", () => {
      renderPage();
      expect(
        screen.getByRole("heading", { name: "Forgot Password" }),
      ).toBeInTheDocument();
    });

    it("renders username and RSI handle fields", () => {
      renderPage();
      expect(screen.getByLabelText("Username")).toBeInTheDocument();
      expect(screen.getByLabelText("RSI Handle")).toBeInTheDocument();
    });

    it("renders continue button", () => {
      renderPage();
      expect(
        screen.getByRole("button", { name: "Continue" }),
      ).toBeInTheDocument();
    });

    it("renders back to login link", () => {
      renderPage();
      const link = screen.getByRole("link", { name: "Back to Login" });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", "/login");
    });

    it("preserves redirect_uri in back to login link", () => {
      renderPage([
        "/password/forgot?redirect_uri=http://localhost:3000/callback&state=xyz",
      ]);
      const link = screen.getByRole("link", { name: "Back to Login" });
      expect(link).toHaveAttribute(
        "href",
        "/login?redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback&state=xyz",
      );
    });

    it("shows validation errors on empty submit", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.click(screen.getByRole("button", { name: "Continue" }));

      expect(screen.getByText("Username is required")).toBeInTheDocument();
      expect(screen.getByText("RSI handle is required")).toBeInTheDocument();
    });

    it("shows RSI handle format error", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "ab");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      expect(
        screen.getByText(
          "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
        ),
      ).toBeInTheDocument();
    });

    it("does not call API when validation fails", async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.click(screen.getByRole("button", { name: "Continue" }));

      expect(mockForgotPassword).not.toHaveBeenCalled();
    });

    it("calls forgotPassword API on valid submit", async () => {
      const response: ForgotPasswordResponse = {
        verification_code: "hxn_alpha-brave-delta-ember",
        message: "Verification code generated",
      };
      mockForgotPassword.mockResolvedValueOnce(response);

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(mockForgotPassword).toHaveBeenCalledWith({
          username: "testuser",
          rsi_handle: "test-handle",
        });
      });
    });

    it("displays API error on failure", async () => {
      mockForgotPassword.mockRejectedValueOnce(new Error("User not found"));

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(screen.getByText("User not found")).toBeInTheDocument();
      });
    });

    it("handles non-Error rejection", async () => {
      mockForgotPassword.mockRejectedValueOnce("unexpected");

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(screen.getByText("Request failed")).toBeInTheDocument();
      });
    });

    it("disables button while submitting", async () => {
      let resolveApi!: (value: ForgotPasswordResponse) => void;
      mockForgotPassword.mockImplementationOnce(
        () =>
          new Promise<ForgotPasswordResponse>((resolve) => {
            resolveApi = resolve;
          }),
      );

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Submitting…" }),
        ).toBeDisabled();
      });

      resolveApi!({
        verification_code: "hxn_test",
        message: "ok",
      });
    });
  });

  describe("Step 2 — Verification Code", () => {
    async function advanceToCodeStep() {
      mockForgotPassword.mockResolvedValueOnce({
        verification_code: "hxn_alpha-brave-delta-ember",
        message: "Verification code generated",
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "RSI Bio Verification" }),
        ).toBeInTheDocument();
      });

      return user;
    }

    it("shows verification code heading", async () => {
      await advanceToCodeStep();

      expect(
        screen.getByRole("heading", { name: "RSI Bio Verification" }),
      ).toBeInTheDocument();
    });

    it("displays the verification code", async () => {
      await advanceToCodeStep();

      expect(
        screen.getByText("hxn_alpha-brave-delta-ember"),
      ).toBeInTheDocument();
    });

    it("shows copy button", async () => {
      await advanceToCodeStep();

      expect(
        screen.getByRole("button", { name: "Copy" }),
      ).toBeInTheDocument();
    });

    it("copies code to clipboard on click", async () => {
      const user = await advanceToCodeStep();

      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "clipboard", {
        value: { writeText },
        writable: true,
        configurable: true,
      });

      await user.click(screen.getByRole("button", { name: "Copy" }));

      await waitFor(() => {
        expect(writeText).toHaveBeenCalledWith("hxn_alpha-brave-delta-ember");
      });
    });

    it("shows 'Copied!' after clicking copy", async () => {
      const user = await advanceToCodeStep();

      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "clipboard", {
        value: { writeText },
        writable: true,
        configurable: true,
      });

      await user.click(screen.getByRole("button", { name: "Copy" }));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Copied!" }),
        ).toBeInTheDocument();
      });
    });

    it("shows RSI profile link", async () => {
      await advanceToCodeStep();

      const link = screen.getByRole("link", { name: "RSI profile bio" });
      expect(link).toHaveAttribute(
        "href",
        "https://robertsspaceindustries.com/account/profile",
      );
      expect(link).toHaveAttribute("target", "_blank");
    });

    it("shows button to proceed to reset step", async () => {
      await advanceToCodeStep();

      expect(
        screen.getByRole("button", {
          name: "I've Updated My RSI Bio",
        }),
      ).toBeInTheDocument();
    });

    it("clicking proceed button moves to reset step", async () => {
      const user = await advanceToCodeStep();

      await user.click(
        screen.getByRole("button", {
          name: "I've Updated My RSI Bio",
        }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Reset Password" }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Step 3 — Reset Password", () => {
    async function advanceToResetStep() {
      mockForgotPassword.mockResolvedValueOnce({
        verification_code: "hxn_alpha-brave-delta-ember",
        message: "Verification code generated",
      });

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "RSI Bio Verification" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", {
          name: "I've Updated My RSI Bio",
        }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Reset Password" }),
        ).toBeInTheDocument();
      });

      return user;
    }

    it("renders new password and confirm fields", async () => {
      await advanceToResetStep();

      expect(screen.getByLabelText("New Password")).toBeInTheDocument();
      expect(screen.getByLabelText("Confirm New Password")).toBeInTheDocument();
    });

    it("renders reset password button", async () => {
      await advanceToResetStep();

      expect(
        screen.getByRole("button", { name: "Reset Password" }),
      ).toBeInTheDocument();
    });

    it("shows validation errors on empty submit", async () => {
      const user = await advanceToResetStep();

      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      expect(screen.getByText("Password is required")).toBeInTheDocument();
      expect(
        screen.getByText("Please confirm your password"),
      ).toBeInTheDocument();
    });

    it("shows min length error for short password", async () => {
      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "short");
      await user.type(screen.getByLabelText("Confirm New Password"), "short");
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      expect(
        screen.getByText("Password must be at least 8 characters"),
      ).toBeInTheDocument();
    });

    it("shows mismatch error when passwords do not match", async () => {
      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword2",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    });

    it("does not call API when validation fails", async () => {
      const user = await advanceToResetStep();

      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      expect(mockConfirmForgotPassword).not.toHaveBeenCalled();
    });

    it("calls confirmForgotPassword API on valid submit", async () => {
      mockConfirmForgotPassword.mockResolvedValueOnce(undefined);
      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(mockConfirmForgotPassword).toHaveBeenCalledWith({
          username: "testuser",
          rsi_handle: "test-handle",
          new_password: "newpassword1",
        });
      });
    });

    it("displays API error on failure", async () => {
      mockConfirmForgotPassword.mockRejectedValueOnce(
        new Error("Verification code not found in RSI bio"),
      );
      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText("Verification code not found in RSI bio"),
        ).toBeInTheDocument();
      });
    });

    it("handles non-Error rejection", async () => {
      mockConfirmForgotPassword.mockRejectedValueOnce("unexpected");
      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(screen.getByText("Password reset failed")).toBeInTheDocument();
      });
    });

    it("disables button while submitting", async () => {
      let resolveApi!: (value: void) => void;
      mockConfirmForgotPassword.mockImplementationOnce(
        () =>
          new Promise<void>((resolve) => {
            resolveApi = resolve;
          }),
      );

      const user = await advanceToResetStep();

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Resetting Password…" }),
        ).toBeDisabled();
      });

      resolveApi!();
    });
  });

  describe("Step 4 — Success", () => {
    async function advanceToSuccess() {
      mockForgotPassword.mockResolvedValueOnce({
        verification_code: "hxn_alpha-brave-delta-ember",
        message: "Verification code generated",
      });
      mockConfirmForgotPassword.mockResolvedValueOnce(undefined);

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "RSI Bio Verification" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", {
          name: "I've Updated My RSI Bio",
        }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Reset Password" }),
        ).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Password Reset!" }),
        ).toBeInTheDocument();
      });

      return user;
    }

    it("shows success heading", async () => {
      await advanceToSuccess();

      expect(
        screen.getByRole("heading", { name: "Password Reset!" }),
      ).toBeInTheDocument();
    });

    it("shows redirect message", async () => {
      await advanceToSuccess();

      expect(screen.getByText("Redirecting to login…")).toBeInTheDocument();
    });

    it("redirects to login after 3 seconds", async () => {
      await advanceToSuccess();

      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      });
    });

    it("preserves redirect_uri in redirect", async () => {
      mockForgotPassword.mockResolvedValueOnce({
        verification_code: "hxn_alpha-brave-delta-ember",
        message: "Verification code generated",
      });
      mockConfirmForgotPassword.mockResolvedValueOnce(undefined);

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage([
        "/password/forgot?redirect_uri=http://localhost:3000/callback&state=xyz",
      ]);

      await user.type(screen.getByLabelText("Username"), "testuser");
      await user.type(screen.getByLabelText("RSI Handle"), "test-handle");
      await user.click(screen.getByRole("button", { name: "Continue" }));

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "RSI Bio Verification" }),
        ).toBeInTheDocument();
      });

      await user.click(
        screen.getByRole("button", {
          name: "I've Updated My RSI Bio",
        }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Reset Password" }),
        ).toBeInTheDocument();
      });

      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Reset Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Password Reset!" }),
        ).toBeInTheDocument();
      });

      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          "/login?redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback&state=xyz",
          { replace: true },
        );
      });
    });
  });
});
