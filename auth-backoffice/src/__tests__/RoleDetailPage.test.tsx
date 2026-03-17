import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import RoleDetailPage from "@/pages/RoleDetailPage";

const mockPermissions = [
  { _id: "p1", code: "hhh:contracts:read", description: "Read contracts" },
  { _id: "p2", code: "hhh:contracts:write", description: "Write contracts" },
  { _id: "p3", code: "auth:users:read", description: "Read users" },
  { _id: "p4", code: "auth:users:admin", description: "Admin users" },
];

const mockRole = {
  _id: "r1",
  name: "Super Admin",
  description: "Full access",
  permission_ids: ["p1", "p2"],
};

vi.mock("@/api/rbac", () => ({
  listPermissions: vi.fn(),
  getRole: vi.fn(),
  createRole: vi.fn(),
  updateRole: vi.fn(),
}));

import * as rbacApi from "@/api/rbac";

function renderPage(id: string = "r1") {
  const router = createMemoryRouter(
    [
      { path: "/rbac/roles/:id", element: <RoleDetailPage /> },
      { path: "/rbac/roles", element: <div>Roles List</div> },
    ],
    { initialEntries: [`/rbac/roles/${id}`] },
  );
  return render(<RouterProvider router={router} />);
}

describe("RoleDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rbacApi.listPermissions).mockResolvedValue(mockPermissions);
    vi.mocked(rbacApi.getRole).mockResolvedValue(mockRole);
  });

  it("renders edit form with existing role data", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("Full access")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Edit Role" })).toBeInTheDocument();
  });

  it("renders new role form", async () => {
    vi.mocked(rbacApi.getRole).mockResolvedValue(mockRole);
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "New Role" })).toBeInTheDocument();
    });
    expect(rbacApi.getRole).not.toHaveBeenCalled();
  });

  it("shows loading state initially", () => {
    vi.mocked(rbacApi.listPermissions).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(rbacApi.listPermissions).mockRejectedValue(new Error("Failed to load"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Failed to load");
    });
  });

  it("groups permissions by service", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("hhh:contracts")).toBeInTheDocument();
    });
    expect(screen.getByText("auth:users")).toBeInTheDocument();
  });

  it("shows checked permissions for existing role", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    // p1 and p2 should be checked
    const contractsRead = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("hhh:contracts:read");
    });
    const contractsWrite = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("hhh:contracts:write");
    });
    const usersRead = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("auth:users:read");
    });
    expect(contractsRead).toBeChecked();
    expect(contractsWrite).toBeChecked();
    expect(usersRead).not.toBeChecked();
  });

  it("toggles permission checkbox", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    const usersRead = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("auth:users:read");
    })!;
    expect(usersRead).not.toBeChecked();
    await user.click(usersRead);
    expect(usersRead).toBeChecked();
  });

  it("saves updated role", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updateRole).mockResolvedValue({
      ...mockRole,
      description: "Updated",
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    const descInput = screen.getByLabelText("Description");
    await user.clear(descInput);
    await user.type(descInput, "Updated");
    await user.click(screen.getByText("Save Changes"));
    await waitFor(() => {
      expect(rbacApi.updateRole).toHaveBeenCalledWith("r1", {
        name: "Super Admin",
        description: "Updated",
        permission_ids: ["p1", "p2"],
      });
    });
  });

  it("creates new role", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.createRole).mockResolvedValue({
      _id: "r-new",
      name: "New Role",
      description: "A new role",
      permission_ids: [],
    });
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("Name")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("Name"), "New Role");
    await user.type(screen.getByLabelText("Description"), "A new role");
    await user.click(screen.getByText("Create Role"));
    await waitFor(() => {
      expect(rbacApi.createRole).toHaveBeenCalledWith({
        name: "New Role",
        description: "A new role",
        permission_ids: [],
      });
    });
  });

  it("shows error when save fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updateRole).mockRejectedValue(new Error("Save failed"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Save Changes"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Save failed");
    });
  });

  it("shows permission descriptions", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Read contracts/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Write contracts/)).toBeInTheDocument();
    expect(screen.getByText(/Read users/)).toBeInTheDocument();
  });

  it("has back link to roles list", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Back to roles")).toBeInTheDocument();
  });

  it("has cancel link", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Super Admin")).toBeInTheDocument();
    });
    expect(screen.getByText("Cancel").closest("a")).toHaveAttribute("href", "/rbac/roles");
  });

  it("shows empty permission state", async () => {
    vi.mocked(rbacApi.listPermissions).mockResolvedValue([]);
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByText("No permissions available.")).toBeInTheDocument();
    });
  });
});
