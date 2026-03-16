import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import PermissionsPage from "@/pages/PermissionsPage";

const mockPermissions = [
  { _id: "p1", code: "contracts:read", description: "Read contracts" },
  { _id: "p2", code: "contracts:write", description: "Write contracts" },
  { _id: "p3", code: "users:read", description: "Read users" },
];

const mockRoles = [
  { _id: "r1", name: "Admin", description: "Admin role", permission_ids: ["p1", "p2"] },
  { _id: "r2", name: "Viewer", description: "Viewer role", permission_ids: ["p3"] },
];

vi.mock("@/api/rbac", () => ({
  listPermissions: vi.fn(),
  listRoles: vi.fn(),
  createPermission: vi.fn(),
  updatePermission: vi.fn(),
  deletePermission: vi.fn(),
}));

import * as rbacApi from "@/api/rbac";

function renderPage() {
  const router = createMemoryRouter(
    [{ path: "/rbac/permissions", element: <PermissionsPage /> }],
    { initialEntries: ["/rbac/permissions"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("PermissionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rbacApi.listPermissions).mockResolvedValue(mockPermissions);
    vi.mocked(rbacApi.listRoles).mockResolvedValue(mockRoles);
  });

  it("renders the permissions table with data", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    expect(screen.getByText("contracts:write")).toBeInTheDocument();
    expect(screen.getByText("users:read")).toBeInTheDocument();
    expect(screen.getByText("Read contracts")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(rbacApi.listPermissions).mockReturnValue(new Promise(() => {}));
    vi.mocked(rbacApi.listRoles).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(rbacApi.listPermissions).mockRejectedValue(new Error("Network error"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("shows empty state when no permissions", async () => {
    vi.mocked(rbacApi.listPermissions).mockResolvedValue([]);
    vi.mocked(rbacApi.listRoles).mockResolvedValue([]);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("No permissions found.")).toBeInTheDocument();
    });
  });

  it("shows create form when New Permission button is clicked", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByText("New Permission"));
    expect(screen.getByTestId("create-form")).toBeInTheDocument();
    expect(screen.getByLabelText("Permission code")).toBeInTheDocument();
    expect(screen.getByLabelText("Permission description")).toBeInTheDocument();
  });

  it("creates a permission when form is submitted", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.createPermission).mockResolvedValue({
      _id: "p4",
      code: "ships:read",
      description: "Read ships",
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByText("New Permission"));
    await user.type(screen.getByLabelText("Permission code"), "ships:read");
    await user.type(screen.getByLabelText("Permission description"), "Read ships");
    await user.click(screen.getByText("Create"));
    await waitFor(() => {
      expect(rbacApi.createPermission).toHaveBeenCalledWith({
        code: "ships:read",
        description: "Read ships",
      });
    });
  });

  it("cancels create form", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByText("New Permission"));
    expect(screen.getByTestId("create-form")).toBeInTheDocument();
    await user.click(screen.getAllByText("Cancel")[0]);
    expect(screen.queryByTestId("create-form")).not.toBeInTheDocument();
  });

  it("enters edit mode when Edit button is clicked", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Edit contracts:read"));
    expect(screen.getByLabelText("Edit permission code")).toBeInTheDocument();
    expect(screen.getByLabelText("Edit permission description")).toBeInTheDocument();
  });

  it("saves edited permission", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updatePermission).mockResolvedValue({
      _id: "p1",
      code: "contracts:read",
      description: "Updated description",
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Edit contracts:read"));
    const descInput = screen.getByLabelText("Edit permission description");
    await user.clear(descInput);
    await user.type(descInput, "Updated description");
    await user.click(screen.getByText("Save"));
    await waitFor(() => {
      expect(rbacApi.updatePermission).toHaveBeenCalledWith("p1", {
        code: "contracts:read",
        description: "Updated description",
      });
    });
  });

  it("cancels edit mode", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Edit contracts:read"));
    expect(screen.getByLabelText("Edit permission code")).toBeInTheDocument();
    await user.click(screen.getAllByText("Cancel")[0]);
    expect(screen.queryByLabelText("Edit permission code")).not.toBeInTheDocument();
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete contracts:read"));
    expect(screen.getByRole("dialog", { name: "Delete confirmation" })).toBeInTheDocument();
    expect(screen.getByText("Are you sure you want to delete this permission?")).toBeInTheDocument();
  });

  it("shows warning when deleting permission assigned to roles", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    // p1 (contracts:read) is assigned to role r1
    await user.click(screen.getByLabelText("Delete contracts:read"));
    expect(screen.getByText(/This permission is assigned to one or more roles/)).toBeInTheDocument();
  });

  it("does not show warning when deleting unassigned permission", async () => {
    vi.mocked(rbacApi.listPermissions).mockResolvedValue([
      { _id: "p99", code: "orphan:perm", description: "Orphan" },
    ]);
    vi.mocked(rbacApi.listRoles).mockResolvedValue([]);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("orphan:perm")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete orphan:perm"));
    expect(screen.queryByText(/This permission is assigned/)).not.toBeInTheDocument();
  });

  it("deletes permission when confirmed", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deletePermission).mockResolvedValue();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete contracts:read"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(rbacApi.deletePermission).toHaveBeenCalledWith("p1");
    });
  });

  it("cancels delete dialog", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete contracts:read"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getAllByText("Cancel")[0]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows error when create fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.createPermission).mockRejectedValue(new Error("Duplicate code"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByText("New Permission"));
    await user.type(screen.getByLabelText("Permission code"), "test:code");
    await user.type(screen.getByLabelText("Permission description"), "Test");
    await user.click(screen.getByText("Create"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Duplicate code");
    });
  });

  it("shows error when update fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updatePermission).mockRejectedValue(new Error("Update failed"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Edit contracts:read"));
    await user.click(screen.getByText("Save"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Update failed");
    });
  });

  it("shows error when delete fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.deletePermission).mockRejectedValue(new Error("Delete failed"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("contracts:read")).toBeInTheDocument();
    });
    await user.click(screen.getByLabelText("Delete contracts:read"));
    await user.click(screen.getByText("Confirm Delete"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Delete failed");
    });
  });

  it("renders page heading", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Permissions" })).toBeInTheDocument();
    });
  });
});
