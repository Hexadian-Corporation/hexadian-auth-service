import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import UserDetailPage from "@/pages/UserDetailPage";
import type { User } from "@/types/user";
import type { Group } from "@/types/rbac";

const mockUser: User = {
  id: "u1",
  username: "alice",
  group_ids: ["g1"],
  is_active: true,
  rsi_handle: "AliceRSI",
  rsi_verified: true,
};

const mockGroups: Group[] = [
  { _id: "g1", name: "Admins", description: "Admin group", role_ids: [] },
  { _id: "g2", name: "Users", description: "User group", role_ids: [] },
];

vi.mock("@/api/users", () => ({
  getUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  resetPassword: vi.fn(),
}));

vi.mock("@/api/rbac", () => ({
  listGroups: vi.fn(),
  assignUserGroup: vi.fn(),
  removeUserGroup: vi.fn(),
}));

import { getUser, updateUser, deleteUser, resetPassword } from "@/api/users";
import { listGroups, assignUserGroup, removeUserGroup } from "@/api/rbac";

function renderUserDetailPage(userId = "u1") {
  const router = createMemoryRouter(
    [
      { path: "/users/:id", element: <UserDetailPage /> },
      { path: "/users", element: <div>Users List</div> },
    ],
    { initialEntries: [`/users/${userId}`] },
  );
  return render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getUser).mockResolvedValue(mockUser);
  vi.mocked(listGroups).mockResolvedValue(mockGroups);
});

describe("UserDetailPage", () => {
  it("renders loading state initially", () => {
    vi.mocked(getUser).mockReturnValue(new Promise(() => {}));
    vi.mocked(listGroups).mockReturnValue(new Promise(() => {}));
    renderUserDetailPage();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders user detail form", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Username")).toHaveValue("alice");
    expect(screen.getByLabelText("RSI Handle")).toHaveValue("AliceRSI");
  });

  it("displays active status badge", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(1);
  });

  it("displays inactive status badge", async () => {
    vi.mocked(getUser).mockResolvedValue({ ...mockUser, is_active: false });
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("displays RSI verified badge", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByText("Verified")).toBeInTheDocument();
  });

  it("displays RSI unverified badge", async () => {
    vi.mocked(getUser).mockResolvedValue({ ...mockUser, rsi_verified: false });
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByText("Unverified")).toBeInTheDocument();
  });

  it("displays current groups as tags", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByText("Admins")).toBeInTheDocument();
  });

  it("shows available groups in add dropdown", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
    expect(screen.getByText("Users")).toBeInTheDocument();
  });

  it("saves updated username", async () => {
    vi.mocked(updateUser).mockResolvedValue({
      ...mockUser,
      username: "alice-updated",
    });
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Username")).toBeInTheDocument();
    });

    const usernameInput = screen.getByLabelText("Username");
    await user.clear(usernameInput);
    await user.type(usernameInput, "alice-updated");
    await user.click(screen.getByRole("button", { name: /Save/ }));

    await waitFor(() => {
      expect(updateUser).toHaveBeenCalledWith("u1", {
        username: "alice-updated",
      });
    });
    expect(screen.getByText("User updated successfully")).toBeInTheDocument();
  });

  it("saves updated RSI handle", async () => {
    vi.mocked(updateUser).mockResolvedValue({
      ...mockUser,
      rsi_handle: "NewHandle",
    });
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByLabelText("RSI Handle")).toBeInTheDocument();
    });

    const rsiInput = screen.getByLabelText("RSI Handle");
    await user.clear(rsiInput);
    await user.type(rsiInput, "NewHandle");
    await user.click(screen.getByRole("button", { name: /Save/ }));

    await waitFor(() => {
      expect(updateUser).toHaveBeenCalledWith("u1", {
        rsi_handle: "NewHandle",
      });
    });
  });

  it("does not call update when no changes", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Username")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Save/ }));
    expect(updateUser).not.toHaveBeenCalled();
    expect(screen.getByText("User updated successfully")).toBeInTheDocument();
  });

  it("shows error when update fails", async () => {
    vi.mocked(updateUser).mockRejectedValue(new Error("Update failed"));
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Username")).toBeInTheDocument();
    });

    const usernameInput = screen.getByLabelText("Username");
    await user.clear(usernameInput);
    await user.type(usernameInput, "newname");
    await user.click(screen.getByRole("button", { name: /Save/ }));

    await waitFor(() => {
      expect(screen.getByText("Update failed")).toBeInTheDocument();
    });
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Delete/ }));
    expect(
      screen.getByText(/Are you sure you want to delete/),
    ).toBeInTheDocument();
  });

  it("deletes user and navigates to list", async () => {
    vi.mocked(deleteUser).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Delete/ }));
    const confirmDelete = screen.getAllByRole("button", { name: /Delete/ });
    await user.click(confirmDelete[confirmDelete.length - 1]);

    await waitFor(() => {
      expect(deleteUser).toHaveBeenCalledWith("u1");
    });
    await waitFor(() => {
      expect(screen.getByText("Users List")).toBeInTheDocument();
    });
  });

  it("cancels delete dialog", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Delete/ }));
    await user.click(screen.getByText("Cancel"));

    expect(screen.queryByText(/Are you sure/)).not.toBeInTheDocument();
  });

  it("shows password reset dialog", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Reset Password/ }));
    expect(screen.getByLabelText("New Password")).toBeInTheDocument();
    expect(screen.getByText(/Set a new password for/)).toBeInTheDocument();
  });

  it("resets password successfully", async () => {
    vi.mocked(resetPassword).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    // Open dialog
    await user.click(screen.getByRole("button", { name: /Reset Password/ }));
    await user.type(screen.getByLabelText("New Password"), "newpass123");

    // Click the dialog's "Reset Password" button (last one)
    const resetButtons = screen.getAllByRole("button", {
      name: "Reset Password",
    });
    await user.click(resetButtons[resetButtons.length - 1]);

    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith("u1", "newpass123");
    });
    expect(
      screen.getByText("Password reset successfully"),
    ).toBeInTheDocument();
  });

  it("shows validation error for short password", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Reset Password/ }));
    await user.type(screen.getByLabelText("New Password"), "short");

    // Click the dialog's "Reset Password" button (last one)
    const resetButtons = screen.getAllByRole("button", {
      name: "Reset Password",
    });
    await user.click(resetButtons[resetButtons.length - 1]);

    expect(
      screen.getByText("Password must be at least 8 characters"),
    ).toBeInTheDocument();
    expect(resetPassword).not.toHaveBeenCalled();
  });

  it("cancels password reset dialog", async () => {
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Reset Password/ }));
    expect(screen.getByLabelText("New Password")).toBeInTheDocument();
    await user.click(screen.getByText("Cancel"));
    expect(screen.queryByLabelText("New Password")).not.toBeInTheDocument();
  });

  it("adds a group to user", async () => {
    vi.mocked(assignUserGroup).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "g2");
    await user.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() => {
      expect(assignUserGroup).toHaveBeenCalledWith("u1", "g2");
    });
  });

  it("removes a group from user", async () => {
    vi.mocked(removeUserGroup).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });

    await user.click(screen.getByTitle("Remove Admins"));

    await waitFor(() => {
      expect(removeUserGroup).toHaveBeenCalledWith("u1", "g1");
    });
  });

  it("shows error when loading user fails", async () => {
    vi.mocked(getUser).mockRejectedValue(new Error("Not found"));
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Not found")).toBeInTheDocument();
    });
    expect(screen.getByText("← Back to Users")).toBeInTheDocument();
  });

  it("shows RSI handle note about verification reset", async () => {
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(
      screen.getByText(
        "Changing the RSI handle will reset RSI verification.",
      ),
    ).toBeInTheDocument();
  });

  it("displays 'No groups assigned' when user has no groups", async () => {
    vi.mocked(getUser).mockResolvedValue({ ...mockUser, group_ids: [] });
    renderUserDetailPage();
    await waitFor(() => {
      expect(screen.getByText("Edit User")).toBeInTheDocument();
    });
    expect(screen.getByText("No groups assigned.")).toBeInTheDocument();
  });
});
