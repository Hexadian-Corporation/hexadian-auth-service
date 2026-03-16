import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import VerifyPage from "@/pages/VerifyPage";
import type { VerificationStartResponse } from "@/types/auth";

vi.mock("@/api/auth", () => ({
  startVerification: vi.fn(),
  confirmVerification: vi.fn(),
  refreshToken: vi.fn(),
}));

vi.mock("@/lib/auth", async () => {
  const actual = await vi.importActual("@/lib/auth");
  return {
    ...actual,
    parseAccessToken: vi.fn(),
    getAccessToken: vi.fn(),
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

import { startVerification, confirmVerification, refreshToken } from "@/api/auth";
import { parseAccessToken, getAccessToken } from "@/lib/auth";
const mockStartVerification = vi.mocked(startVerification);
const mockConfirmVerification = vi.mocked(confirmVerification);
const mockRefreshToken = vi.mocked(refreshToken);
const mockParseAccessToken = vi.mocked(parseAccessToken);
const mockGetAccessToken = vi.mocked(getAccessToken);

function renderPage() {
  return render(
    <MemoryRouter>
      <VerifyPage />
    </MemoryRouter>,
  );
}

function setupAuthenticatedUser(overrides?: {
  rsi_handle?: string | null;
  rsi_verified?: boolean;
}) {
  mockParseAccessToken.mockReturnValue({
    sub: "user-1",
    username: "testuser",
    rsi_handle:
      overrides && "rsi_handle" in overrides
        ? (overrides.rsi_handle as string | null)
        : "test-handle",
    rsi_verified: overrides?.rsi_verified ?? false,
  });
  mockGetAccessToken.mockReturnValue("mock-access-token");
}

describe("VerifyPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("authentication", () => {
    it("redirects to login when not authenticated", () => {
      mockParseAccessToken.mockReturnValue(null);
      renderPage();

      expect(mockNavigate).toHaveBeenCalledWith(
        "/login?redirect_uri=/verify",
        { replace: true },
      );
    });

    it("renders nothing when not authenticated", () => {
      mockParseAccessToken.mockReturnValue(null);
      const { container } = renderPage();

      expect(container.firstChild).toBeNull();
    });
  });

  describe("status display", () => {
    it("renders the RSI Verification heading", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(
        screen.getByRole("heading", { name: "RSI Verification" }),
      ).toBeInTheDocument();
    });

    it("shows RSI handle as link", () => {
      setupAuthenticatedUser({ rsi_handle: "my-handle" });
      renderPage();

      const link = screen.getByRole("link", { name: "my-handle" });
      expect(link).toHaveAttribute(
        "href",
        "https://robertsspaceindustries.com/citizens/my-handle",
      );
      expect(link).toHaveAttribute("target", "_blank");
    });

    it("shows 'Not set' when rsi_handle is null", () => {
      setupAuthenticatedUser({ rsi_handle: null });
      renderPage();

      expect(screen.getByText("Not set")).toBeInTheDocument();
    });

    it("shows 'Not Verified' badge when not verified", () => {
      setupAuthenticatedUser({ rsi_verified: false });
      renderPage();

      expect(screen.getByText("Not Verified")).toBeInTheDocument();
    });

    it("shows 'Verified' badge when verified", () => {
      setupAuthenticatedUser({ rsi_verified: true });
      renderPage();

      expect(screen.getByText("Verified")).toBeInTheDocument();
    });

    it("shows verified message when already verified", () => {
      setupAuthenticatedUser({ rsi_verified: true });
      renderPage();

      expect(
        screen.getByText("Your RSI identity has been verified."),
      ).toBeInTheDocument();
    });

    it("does not show Start Verification button when already verified", () => {
      setupAuthenticatedUser({ rsi_verified: true });
      renderPage();

      expect(
        screen.queryByRole("button", { name: "Start Verification" }),
      ).not.toBeInTheDocument();
    });

    it("does not show Start Verification when rsi_handle is null", () => {
      setupAuthenticatedUser({ rsi_handle: null, rsi_verified: false });
      renderPage();

      expect(
        screen.queryByRole("button", { name: "Start Verification" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("start verification", () => {
    it("shows Start Verification button when not verified", () => {
      setupAuthenticatedUser();
      renderPage();

      expect(
        screen.getByRole("button", { name: "Start Verification" }),
      ).toBeInTheDocument();
    });

    it("calls startVerification and shows verification code", async () => {
      setupAuthenticatedUser();
      const response: VerificationStartResponse = {
        verification_code: "Hexadian account validation code: alpha-bravo-charlie-delta-echo-foxtrot",
        verified: false,
        message: "Code generated",
      };
      mockStartVerification.mockResolvedValueOnce(response);

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(mockStartVerification).toHaveBeenCalledWith(
          { rsi_handle: "test-handle" },
          "mock-access-token",
        );
      });

      expect(
        screen.getByText(
          "Hexadian account validation code: alpha-bravo-charlie-delta-echo-foxtrot",
        ),
      ).toBeInTheDocument();
    });

    it("sets verified state when startVerification returns verified=true", async () => {
      setupAuthenticatedUser();
      const response: VerificationStartResponse = {
        verification_code: null,
        verified: true,
        message: "Already verified",
      };
      mockStartVerification.mockResolvedValueOnce(response);

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("Verified")).toBeInTheDocument();
      });
    });

    it("shows error on startVerification failure", async () => {
      setupAuthenticatedUser();
      mockStartVerification.mockRejectedValueOnce(
        new Error("Server error"),
      );

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
    });

    it("shows generic error for non-Error rejection in start", async () => {
      setupAuthenticatedUser();
      mockStartVerification.mockRejectedValueOnce("unexpected");

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText("Failed to start verification"),
        ).toBeInTheDocument();
      });
    });

    it("disables button while starting verification", async () => {
      setupAuthenticatedUser();
      let resolveStart!: (value: VerificationStartResponse) => void;
      mockStartVerification.mockImplementationOnce(
        () =>
          new Promise<VerificationStartResponse>((resolve) => {
            resolveStart = resolve;
          }),
      );

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Starting…" }),
        ).toBeDisabled();
      });

      resolveStart({
        verification_code: "test-code",
        verified: false,
        message: "ok",
      });
    });
  });

  describe("verification code display", () => {
    async function renderWithCode() {
      setupAuthenticatedUser();
      mockStartVerification.mockResolvedValueOnce({
        verification_code: "test-verification-code",
        verified: false,
        message: "Code generated",
      });

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("test-verification-code")).toBeInTheDocument();
      });

      return user;
    }

    it("shows copy button alongside code", async () => {
      await renderWithCode();

      expect(
        screen.getByRole("button", { name: "Copy" }),
      ).toBeInTheDocument();
    });

    it("copies code to clipboard on click", async () => {
      const user = await renderWithCode();

      // Define mock after renderWithCode so userEvent.setup() doesn't replace it
      const writeText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "clipboard", {
        value: { writeText },
        writable: true,
        configurable: true,
      });

      await user.click(screen.getByRole("button", { name: "Copy" }));

      await waitFor(() => {
        expect(writeText).toHaveBeenCalledWith("test-verification-code");
      });
    });

    it("shows 'Copied!' after clicking copy", async () => {
      const user = await renderWithCode();

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

    it("shows RSI profile edit link", async () => {
      await renderWithCode();

      const link = screen.getByRole("link", { name: "RSI profile bio" });
      expect(link).toHaveAttribute(
        "href",
        "https://robertsspaceindustries.com/account/profile",
      );
      expect(link).toHaveAttribute("target", "_blank");
    });

    it("shows Confirm Verification button", async () => {
      await renderWithCode();

      expect(
        screen.getByRole("button", { name: "Confirm Verification" }),
      ).toBeInTheDocument();
    });
  });

  describe("confirm verification", () => {
    async function renderWithCodeAndConfirm() {
      setupAuthenticatedUser();
      mockStartVerification.mockResolvedValueOnce({
        verification_code: "test-code",
        verified: false,
        message: "ok",
      });

      const user = userEvent.setup();
      renderPage();

      await user.click(
        screen.getByRole("button", { name: "Start Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("test-code")).toBeInTheDocument();
      });

      return user;
    }

    it("calls confirmVerification and shows verified on success", async () => {
      const user = await renderWithCodeAndConfirm();

      mockConfirmVerification.mockResolvedValueOnce({
        verification_code: null,
        verified: true,
        message: "Verified",
      });
      mockRefreshToken.mockResolvedValueOnce({
        access_token: "new-access",
        refresh_token: "new-refresh",
        token_type: "bearer",
        expires_in: 3600,
      });
      // After refreshing, parseAccessToken returns updated payload
      mockParseAccessToken.mockReturnValue({
        sub: "user-1",
        username: "testuser",
        rsi_handle: "test-handle",
        rsi_verified: true,
      });

      localStorage.setItem("refresh_token", "test-refresh");

      await user.click(
        screen.getByRole("button", { name: "Confirm Verification" }),
      );

      await waitFor(() => {
        expect(mockConfirmVerification).toHaveBeenCalledWith(
          { rsi_handle: "test-handle" },
          "mock-access-token",
        );
      });

      await waitFor(() => {
        expect(screen.getByText("Verified")).toBeInTheDocument();
      });

      expect(
        screen.getByText("Your RSI identity has been verified."),
      ).toBeInTheDocument();
    });

    it("shows error when verification fails (not verified)", async () => {
      const user = await renderWithCodeAndConfirm();

      mockConfirmVerification.mockResolvedValueOnce({
        verification_code: null,
        verified: false,
        message: "Not found",
      });

      await user.click(
        screen.getByRole("button", { name: "Confirm Verification" }),
      );

      await waitFor(() => {
        expect(
          screen.getByText(
            "Code not found in your RSI profile bio. Make sure you saved your profile.",
          ),
        ).toBeInTheDocument();
      });
    });

    it("shows error on confirmVerification API failure", async () => {
      const user = await renderWithCodeAndConfirm();

      mockConfirmVerification.mockRejectedValueOnce(
        new Error("Network error"),
      );

      await user.click(
        screen.getByRole("button", { name: "Confirm Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("shows generic error for non-Error rejection in confirm", async () => {
      const user = await renderWithCodeAndConfirm();

      mockConfirmVerification.mockRejectedValueOnce("unexpected");

      await user.click(
        screen.getByRole("button", { name: "Confirm Verification" }),
      );

      await waitFor(() => {
        expect(screen.getByText("Verification failed")).toBeInTheDocument();
      });
    });

    it("disables button while confirming", async () => {
      const user = await renderWithCodeAndConfirm();

      let resolveConfirm!: (value: VerificationStartResponse) => void;
      mockConfirmVerification.mockImplementationOnce(
        () =>
          new Promise<VerificationStartResponse>((resolve) => {
            resolveConfirm = resolve;
          }),
      );

      await user.click(
        screen.getByRole("button", { name: "Confirm Verification" }),
      );

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Confirming…" }),
        ).toBeDisabled();
      });

      resolveConfirm({
        verification_code: null,
        verified: true,
        message: "ok",
      });
    });
  });
});
