import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import RolesPage from "@/pages/RolesPage";

const mockRoles = [
  { _id: "r1", name: "Super Admin", description: "Full access", permission_ids: ["p1", "p2", "p3"] },
  { _id: "r2", name: "Viewer", description: "Read only", permission_ids: ["p1"] },
];

const mockGroups = [
  { _id: "g1", name: "Admins", description: "Admin group", role_ids: ["r1"] },
  { _id: "g2", name: "Users", description: "User group", role_ids: [] },
];

vi.mock("@/api/rbac", () => ({
  listRoles: vi.fn(),
  listGroups: vi.fn(),
  deleteRole: vi.fn(),
}));

import * as rbacApi from "@/api/rbac";

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: "/rbac/roles", element: <RolesPage /> },
      { path: "/rbac/roles/:id", element: <div>Role Detail</div> },
    ],
    { initialEntries: ["/rbac/roles"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("RolesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rbacApi.listRoles).mockResolvedValue(mockRoles);
    vi.mocked(rbacApi.listGroups).mockResolvedValue(mockGroups);
  });

  it("renders the roles table with data", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    expect(screen.getByText("Viewer")).toBeInTheDocument();
    expect(screen.getByText("Full access")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(rbacApi.listRoles).mockReturnValue(new Promise(() => {}));
    vi.mocked(rbacApi.listGroups).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(rbacApi.listRoles).mockRejectedValue(new Error("Network error"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("shows empty state when no roles", async () => {
    vi.mocked(rbacApi.listRoles).mockResolvedValue([]);
    vi.mocked(rbacApi.listGroups).mockResolvedValue([]);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("No roles found.")).toBeInTheDocument();
    });
  });

  it("shows permission count for each role", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    // Super Admin has 3 permissions, Viewer has 1
    const rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("3");
    expect(rows[2]).toHaveTextContent("1");
  });

  it("has New Role link", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("New Role")).toBeInTheDocument();
    });
    expect(screen.getByText("New Role").closest("a")).toHaveAttribute("href", "/rbac/roles/new");
  });

  it("has Edit links for each role", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    const editLinks = screen.getAllByText("Edit");
    expect(editLinks[0].closest("a")).toHaveAttribute("href", "/rbac/roles/r1");
    expect(editLinks[1].closest("a")).toHaveAttribute("href", "/rbac/roles/r2");
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Super Admin"));
    expect(screen.getByRole("dialog", { name: "Delete confirmation" })).toBeInTheDocument();
  });

  it("shows warning when deleting role assigned to groups", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Super Admin"));
    expect(screen.getByText(/This role is assigned to one or more groups/)).toBeInTheDocument();
  });

  it("does not show warning when deleting unassigned role", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Viewer")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Viewer"));
    expect(screen.queryByText(/This role is assigned/)).not.toBeInTheDocument();
  });

  it("deletes role when confirmed", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deleteRole).mockResolvedValue();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Super Admin"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(rbacApi.deleteRole).toHaveBeenCalledWith("r1");
    });
  });

  it("cancels delete dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Super Admin"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getAllByText("Cancel")[0]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows error when delete fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deleteRole).mockRejectedValue(new Error("Cannot delete"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete Super Admin"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Cannot delete");
    });
  });

  it("renders page heading", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Roles" })).toBeInTheDocument();
    });
  });
});
