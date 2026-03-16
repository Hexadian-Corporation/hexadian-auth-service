import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import GroupsPage from "@/pages/GroupsPage";

const mockGroups = [
  { _id: "g1", name: "Admins", description: "Administrator group", role_ids: ["r1", "r2"] },
  { _id: "g2", name: "Users", description: "Default user group", role_ids: ["r3"] },
];

const mockUsers = [
  { _id: "u1", username: "admin", group_ids: ["g1"] },
  { _id: "u2", username: "user1", group_ids: ["g2"] },
  { _id: "u3", username: "user2", group_ids: ["g2"] },
];

vi.mock("@/api/rbac", () => ({
  listGroups: vi.fn(),
  listUsers: vi.fn(),
  deleteGroup: vi.fn(),
}));

import * as rbacApi from "@/api/rbac";

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: "/rbac/groups", element: <GroupsPage /> },
      { path: "/rbac/groups/:id", element: <div>Group Detail</div> },
    ],
    { initialEntries: ["/rbac/groups"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("GroupsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rbacApi.listGroups).mockResolvedValue(mockGroups);
    vi.mocked(rbacApi.listUsers).mockResolvedValue(mockUsers);
  });

  it("renders the groups table with data", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Administrator group")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(rbacApi.listGroups).mockReturnValue(new Promise(() => {}));
    vi.mocked(rbacApi.listUsers).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(rbacApi.listGroups).mockRejectedValue(new Error("Network error"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("shows empty state when no groups", async () => {
    vi.mocked(rbacApi.listGroups).mockResolvedValue([]);
    vi.mocked(rbacApi.listUsers).mockResolvedValue([]);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("No groups found.")).toBeInTheDocument();
    });
  });

  it("shows role count and member count", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    const rows = screen.getAllByRole("row");
    // Admins: 2 roles, 1 member
    expect(rows[1]).toHaveTextContent("2");
    expect(rows[1]).toHaveTextContent("1");
    // Users: 1 role, 2 members
    expect(rows[2]).toHaveTextContent("1");
    expect(rows[2]).toHaveTextContent("2");
  });

  it("has New Group link", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("New Group")).toBeInTheDocument();
    });
    expect(screen.getByText("New Group").closest("a")).toHaveAttribute("href", "/rbac/groups/new");
  });

  it("has Edit links for each group", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    const editLinks = screen.getAllByText("Edit");
    expect(editLinks[0].closest("a")).toHaveAttribute("href", "/rbac/groups/g1");
    expect(editLinks[1].closest("a")).toHaveAttribute("href", "/rbac/groups/g2");
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Admins"));
    expect(screen.getByRole("dialog", { name: "Delete confirmation" })).toBeInTheDocument();
  });

  it("shows warning when deleting group with members", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Users")).toBeInTheDocument();
    });
    // g2 (Users) has 2 members
    await user.click(screen.getByLabelText("Delete Users"));
    expect(screen.getByText(/This group has 2 member/)).toBeInTheDocument();
  });

  it("does not show member warning for group without members", async () => {
    vi.mocked(rbacApi.listUsers).mockResolvedValue([]);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Admins"));
    expect(screen.queryByText(/This group has/)).not.toBeInTheDocument();
  });

  it("deletes group when confirmed", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deleteGroup).mockResolvedValue();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Admins"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(rbacApi.deleteGroup).toHaveBeenCalledWith("g1");
    });
  });

  it("cancels delete dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Admins"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getAllByText("Cancel")[0]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows error when delete fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deleteGroup).mockRejectedValue(new Error("Cannot delete"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Admins"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Cannot delete");
    });
  });

  it("renders page heading", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Groups" })).toBeInTheDocument();
    });
  });
});
