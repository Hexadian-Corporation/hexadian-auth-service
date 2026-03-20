import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChangePasswordPage from "@/pages/ChangePasswordPage";

vi.mock("@/api/auth", () => ({
  changePassword: vi.fn(),
  refreshToken: vi.fn(),
}));

vi.mock("@/lib/auth", async () => {
  const actual = await vi.importActual("@/lib/auth");
  return {
    ...actual,
    parseAccessToken: vi.fn(),
    getAccessToken: vi.fn(),
    clearTokens: vi.fn(),
  };
});

const mockNavigate = vi.fn();
vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { changePassword } from "@/api/auth";
import { parseAccessToken, getAccessToken, clearTokens } from "@/lib/auth";
const mockChangePassword = vi.mocked(changePassword);
const mockParseAccessToken = vi.mocked(parseAccessToken);
const mockGetAccessToken = vi.mocked(getAccessToken);
const mockClearTokens = vi.mocked(clearTokens);

function renderPage() {
  return render(
    <MemoryRouter>
      <ChangePasswordPage />
    </MemoryRouter>,
  );
}

function setupAuthenticatedUser() {
  mockParseAccessToken.mockReturnValue({
    userId: "user-1",
    username: "testuser",
    groups: [],
    roles: [],
    permissions: [],
    rsiHandle: "test-handle",
    rsiVerified: false,
  });
  mockGetAccessToken.mockReturnValue("mock-access-token");
}

describe("ChangePasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("authentication", () => {
    it("redirects to login when not authenticated", () => {
      mockParseAccessToken.mockReturnValue(null);
      renderPage();

      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    it("renders nothing when not authenticated", () => {
      mockParseAccessToken.mockReturnValue(null);
      const { container } = renderPage();

      expect(container.firstChild).toBeNull();
    });
  });

  describe("rendering", () => {
    it("renders the change password heading", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(
        screen.getByRole("heading", { name: "Change Password" }),
      ).toBeInTheDocument();
    });

    it("renders current password, new password, and confirm fields", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(screen.getByLabelText("Current Password")).toBeInTheDocument();
      expect(screen.getByLabelText("New Password")).toBeInTheDocument();
      expect(screen.getByLabelText("Confirm New Password")).toBeInTheDocument();
    });

    it("renders submit button", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(
        screen.getByRole("button", { name: "Change Password" }),
      ).toBeInTheDocument();
    });

    it("informs user about session revocation", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(
        screen.getByText(/all sessions will be revoked/i),
      ).toBeInTheDocument();
    });
  });

  describe("validation", () => {
    it("shows validation errors on empty submit", async () => {
      setupAuthenticatedUser();
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      expect(
        screen.getByText("Current password is required"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Password is required"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Please confirm your password"),
      ).toBeInTheDocument();
    });

    it("shows min length error for short new password", async () => {
      setupAuthenticatedUser();
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "short");
      await user.type(screen.getByLabelText("Confirm New Password"), "short");
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      expect(
        screen.getByText("Password must be at least 8 characters"),
      ).toBeInTheDocument();
    });

    it("shows mismatch error when passwords do not match", async () => {
      setupAuthenticatedUser();
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword2",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    });

    it("does not call API when validation fails", async () => {
      setupAuthenticatedUser();
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      expect(mockChangePassword).not.toHaveBeenCalled();
    });
  });

  describe("successful password change", () => {
    it("calls changePassword API on valid submit", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockResolvedValueOnce(undefined);
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(mockChangePassword).toHaveBeenCalledWith(
          { old_password: "oldpass123", new_password: "newpassword1" },
          "mock-access-token",
        );
      });
    });

    it("shows success message after password change", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockResolvedValueOnce(undefined);
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText(/password changed successfully/i),
        ).toBeInTheDocument();
      });
    });

    it("clears tokens after successful password change", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockResolvedValueOnce(undefined);
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(mockClearTokens).toHaveBeenCalled();
      });
    });

    it("redirects to login after timeout", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockResolvedValueOnce(undefined);
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText(/password changed successfully/i),
        ).toBeInTheDocument();
      });

      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      });
    });
  });

  describe("error handling", () => {
    it("displays API error on failure", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockRejectedValueOnce(
        new Error("Old password is incorrect"),
      );
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "wrongpass");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText("Old password is incorrect"),
        ).toBeInTheDocument();
      });
    });

    it("handles non-Error rejection", async () => {
      setupAuthenticatedUser();
      mockChangePassword.mockRejectedValueOnce("unexpected");
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      renderPage();

      await user.type(screen.getByLabelText("Current Password"), "oldpass123");
      await user.type(screen.getByLabelText("New Password"), "newpassword1");
      await user.type(
        screen.getByLabelText("Confirm New Password"),
        "newpassword1",
      );
      await user.click(
        screen.getByRole("button", { name: "Change Password" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText("Failed to change password"),
        ).toBeInTheDocument();
      });
    });
  });

  it("disables submit button while submitting", async () => {
    setupAuthenticatedUser();
    let resolveChangePassword!: (value: void) => void;
    mockChangePassword.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          resolveChangePassword = resolve;
        }),
    );

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderPage();

    await user.type(screen.getByLabelText("Current Password"), "oldpass123");
    await user.type(screen.getByLabelText("New Password"), "newpassword1");
    await user.type(
      screen.getByLabelText("Confirm New Password"),
      "newpassword1",
    );
    await user.click(
      screen.getByRole("button", { name: "Change Password" }),
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Changing Password…" }),
      ).toBeDisabled();
    });

    resolveChangePassword!();
  });
});
