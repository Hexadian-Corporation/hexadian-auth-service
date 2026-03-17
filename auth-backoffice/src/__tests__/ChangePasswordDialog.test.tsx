import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import DashboardLayout from "@/layouts/DashboardLayout";

vi.mock("@/api/auth", () => ({
  changePassword: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({
  clearTokens: vi.fn(),
  redirectToPortal: vi.fn(),
  getAccessToken: vi.fn(() => "mock-token"),
  authFetch: vi.fn(),
}));

import { changePassword } from "@/api/auth";
import { clearTokens } from "@/lib/auth";

function renderWithLayout() {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <DashboardLayout />,
        children: [{ path: "users", element: <div>Users Page</div> }],
      },
    ],
    { initialEntries: ["/users"] },
  );
  return render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("ChangePasswordDialog", () => {
  it("renders Change Password button in sidebar", () => {
    renderWithLayout();
    expect(screen.getByRole("button", { name: "Change Password" })).toBeInTheDocument();
  });

  it("Change Password button appears above Sign out", () => {
    renderWithLayout();
    const changeBtn = screen.getByRole("button", { name: "Change Password" });
    const signOutBtn = screen.getByRole("button", { name: "Sign out" });
    // changeBtn should come before signOutBtn in DOM order
    expect(changeBtn.compareDocumentPosition(signOutBtn) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("opens dialog when clicking Change Password", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));
    expect(screen.getByLabelText("Current Password")).toBeInTheDocument();
    expect(screen.getByLabelText("New Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm New Password")).toBeInTheDocument();
  });

  it("does not render dialog fields when closed", () => {
    renderWithLayout();
    expect(screen.queryByLabelText("Current Password")).not.toBeInTheDocument();
  });

  it("shows validation error when all fields are empty", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    // Submit empty form
    const submitButtons = screen.getAllByRole("button", { name: "Change Password" });
    await user.click(submitButtons[submitButtons.length - 1]);

    expect(screen.getByText("Current password is required")).toBeInTheDocument();
    expect(screen.getByText("New password is required")).toBeInTheDocument();
    expect(screen.getByText("Please confirm your new password")).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("shows validation error for short new password", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await user.type(screen.getByLabelText("Current Password"), "oldpass");
    await user.type(screen.getByLabelText("New Password"), "short");
    await user.type(screen.getByLabelText("Confirm New Password"), "short");

    const submitButtons = screen.getAllByRole("button", { name: "Change Password" });
    await user.click(submitButtons[submitButtons.length - 1]);

    expect(screen.getByText("Password must be at least 8 characters")).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("shows validation error when passwords do not match", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await user.type(screen.getByLabelText("Current Password"), "oldpassword");
    await user.type(screen.getByLabelText("New Password"), "newpassword123");
    await user.type(screen.getByLabelText("Confirm New Password"), "differentpassword");

    const submitButtons = screen.getAllByRole("button", { name: "Change Password" });
    await user.click(submitButtons[submitButtons.length - 1]);

    expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("calls changePassword and shows success on valid submit", async () => {
    vi.mocked(changePassword).mockResolvedValue(undefined);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await user.type(screen.getByLabelText("Current Password"), "oldpassword");
    await user.type(screen.getByLabelText("New Password"), "newpassword123");
    await user.type(screen.getByLabelText("Confirm New Password"), "newpassword123");

    const submitButtons = screen.getAllByRole("button", { name: "Change Password" });
    await user.click(submitButtons[submitButtons.length - 1]);

    await waitFor(() => {
      expect(changePassword).toHaveBeenCalledWith("oldpassword", "newpassword123");
    });
    expect(screen.getByText("Password changed successfully. You will be redirected to login.")).toBeInTheDocument();
    expect(clearTokens).toHaveBeenCalled();
  });

  it("shows API error on failure", async () => {
    vi.mocked(changePassword).mockRejectedValue(new Error("Current password is incorrect"));
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await user.type(screen.getByLabelText("Current Password"), "wrongpassword");
    await user.type(screen.getByLabelText("New Password"), "newpassword123");
    await user.type(screen.getByLabelText("Confirm New Password"), "newpassword123");

    const submitButtons = screen.getAllByRole("button", { name: "Change Password" });
    await user.click(submitButtons[submitButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Current password is incorrect");
    });
  });

  it("closes dialog on Cancel without side effects", async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderWithLayout();
    await user.click(screen.getByRole("button", { name: "Change Password" }));
    expect(screen.getByLabelText("Current Password")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByLabelText("Current Password")).not.toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
    expect(clearTokens).not.toHaveBeenCalled();
  });
});
