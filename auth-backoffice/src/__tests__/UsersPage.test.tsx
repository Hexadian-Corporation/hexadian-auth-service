import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import UsersPage from "@/pages/UsersPage";
import type { User } from "@/types/user";
import type { Group } from "@/types/rbac";

const mockUsers: User[] = [
  {
    _id: "u1",
    username: "alice",
    group_ids: ["g1"],
    is_active: true,
    rsi_handle: "AliceRSI",
    rsi_verified: true,
  },
  {
    _id: "u2",
    username: "bob",
    group_ids: ["g1", "g2"],
    is_active: false,
    rsi_handle: "BobRSI",
    rsi_verified: false,
  },
  {
    _id: "u3",
    username: "charlie",
    group_ids: [],
    is_active: true,
    rsi_handle: "",
    rsi_verified: false,
  },
];

const mockGroups: Group[] = [
  { _id: "g1", name: "Admins", description: "Admin group", role_ids: [], auto_assign_apps: [] },
  { _id: "g2", name: "Users", description: "User group", role_ids: [], auto_assign_apps: [] },
];

vi.mock("@/api/users", () => ({
  listUsers: vi.fn(),
  deleteUser: vi.fn(),
}));

vi.mock("@/api/rbac", () => ({
  listGroups: vi.fn(),
}));

import { listUsers, deleteUser } from "@/api/users";
import { listGroups } from "@/api/rbac";

function renderUsersPage() {
  const router = createMemoryRouter(
    [{ path: "/users", element: <UsersPage /> }],
    { initialEntries: ["/users"] },
  );
  return render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listUsers).mockResolvedValue(mockUsers);
  vi.mocked(listGroups).mockResolvedValue(mockGroups);
});

describe("UsersPage", () => {
  it("renders loading state initially", () => {
    vi.mocked(listUsers).mockReturnValue(new Promise(() => {}));
    vi.mocked(listGroups).mockReturnValue(new Promise(() => {}));
    renderUsersPage();
    expect(screen.getByText("Loading users…")).toBeInTheDocument();
  });

  it("renders user table with data", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    expect(screen.getByText("bob")).toBeInTheDocument();
    expect(screen.getByText("charlie")).toBeInTheDocument();
  });

  it("displays group names as tags", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    // "Admins" appears as a group tag for alice and bob
    expect(screen.getAllByText("Admins")).toHaveLength(2);
    // "Users" appears as sidebar nav + group tag for bob — check tag exists in table
    const rows = screen.getAllByRole("row");
    const bobRow = rows.find((r) => r.textContent?.includes("bob"));
    expect(bobRow?.textContent).toContain("Users");
  });

  it("displays RSI verified badges", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getAllByText("Unverified")).toHaveLength(2);
  });

  it("displays active/inactive badges", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    // "Active" appears in the table header + as badge for alice and charlie = 3
    expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("displays RSI handles", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("AliceRSI")).toBeInTheDocument();
    });
    expect(screen.getByText("BobRSI")).toBeInTheDocument();
  });

  it("filters users by username", async () => {
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(
      "Filter by username or RSI handle…",
    );
    await user.type(searchInput, "alice");

    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.queryByText("bob")).not.toBeInTheDocument();
    expect(screen.queryByText("charlie")).not.toBeInTheDocument();
  });

  it("filters users by RSI handle", async () => {
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(
      "Filter by username or RSI handle…",
    );
    await user.type(searchInput, "BobRSI");

    expect(screen.getByText("bob")).toBeInTheDocument();
    expect(screen.queryByText("alice")).not.toBeInTheDocument();
  });

  it("shows empty message when no users match filter", async () => {
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(
      "Filter by username or RSI handle…",
    );
    await user.type(searchInput, "nonexistent");

    expect(
      screen.getByText("No users match your filter."),
    ).toBeInTheDocument();
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle("Delete user");
    await user.click(deleteButtons[0]);

    expect(screen.getByText("Delete User")).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to delete/),
    ).toBeInTheDocument();
  });

  it("cancels delete dialog", async () => {
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle("Delete user");
    await user.click(deleteButtons[0]);

    expect(screen.getByText("Delete User")).toBeInTheDocument();
    await user.click(screen.getByText("Cancel"));
    expect(screen.queryByText(/Are you sure/)).not.toBeInTheDocument();
  });

  it("deletes user and removes from table", async () => {
    vi.mocked(deleteUser).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle("Delete user");
    await user.click(deleteButtons[0]);

    // Click the "Delete" button inside the confirmation dialog
    const dialogDeleteBtn = screen.getAllByRole("button", { name: "Delete" });
    await user.click(dialogDeleteBtn[dialogDeleteBtn.length - 1]);

    await waitFor(() => {
      expect(screen.queryByText("alice")).not.toBeInTheDocument();
    });
    expect(deleteUser).toHaveBeenCalledWith("u1");
  });

  it("shows error when loading fails", async () => {
    vi.mocked(listUsers).mockRejectedValue(new Error("Network error"));
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("shows 'None' when user has no groups", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("charlie")).toBeInTheDocument();
    });
    expect(screen.getByText("None")).toBeInTheDocument();
  });

  it("renders edit buttons for each user", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    expect(screen.getAllByTitle("View / Edit")).toHaveLength(3);
  });

  it("shows dash for empty RSI handle", async () => {
    renderUsersPage();
    await waitFor(() => {
      expect(screen.getByText("charlie")).toBeInTheDocument();
    });
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
