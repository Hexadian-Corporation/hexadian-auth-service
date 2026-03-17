import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import GroupDetailPage from "@/pages/GroupDetailPage";

const mockPermissions = [
  { _id: "p1", code: "contracts:read", description: "Read contracts" },
  { _id: "p2", code: "contracts:write", description: "Write contracts" },
  { _id: "p3", code: "users:read", description: "Read users" },
];

const mockRoles = [
  { _id: "r1", name: "Admin", description: "Full access", permission_ids: ["p1", "p2", "p3"] },
  { _id: "r2", name: "Viewer", description: "Read only", permission_ids: ["p1"] },
];

const mockGroup = {
  _id: "g1",
  name: "Admins",
  description: "Administrator group",
  role_ids: ["r1"],
  auto_assign_apps: [],
};

const mockUsers = [
  { _id: "u1", username: "admin", group_ids: ["g1"] },
  { _id: "u2", username: "regular", group_ids: ["g2"] },
];

vi.mock("@/api/rbac", () => ({
  listRoles: vi.fn(),
  listPermissions: vi.fn(),
  listUsers: vi.fn(),
  getGroup: vi.fn(),
  createGroup: vi.fn(),
  updateGroup: vi.fn(),
}));

import * as rbacApi from "@/api/rbac";

function renderPage(id: string = "g1") {
  const router = createMemoryRouter(
    [
      { path: "/rbac/groups/:id", element: <GroupDetailPage /> },
      { path: "/rbac/groups", element: <div>Groups List</div> },
    ],
    { initialEntries: [`/rbac/groups/${id}`] },
  );
  return render(<RouterProvider router={router} />);
}

describe("GroupDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(rbacApi.listRoles).mockResolvedValue(mockRoles);
    vi.mocked(rbacApi.listPermissions).mockResolvedValue(mockPermissions);
    vi.mocked(rbacApi.listUsers).mockResolvedValue(mockUsers);
    vi.mocked(rbacApi.getGroup).mockResolvedValue(mockGroup);
  });

  it("renders edit form with existing group data", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("Administrator group")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Edit Group" })).toBeInTheDocument();
  });

  it("renders new group form", async () => {
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "New Group" })).toBeInTheDocument();
    });
    expect(rbacApi.getGroup).not.toHaveBeenCalled();
  });

  it("shows loading state initially", () => {
    vi.mocked(rbacApi.listRoles).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(rbacApi.listRoles).mockRejectedValue(new Error("Failed to load"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Failed to load");
    });
  });

  it("shows roles with checkboxes", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admin")).toBeInTheDocument();
    });
    expect(screen.getByText("Viewer")).toBeInTheDocument();
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBe(2);
  });

  it("shows checked roles for existing group", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    // r1 (Admin) should be checked, r2 (Viewer) should not
    const adminCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("Admin") && !label?.textContent?.startsWith("Viewer");
    });
    const viewerCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("Viewer");
    });
    expect(adminCheckbox).toBeChecked();
    expect(viewerCheckbox).not.toBeChecked();
  });

  it("toggles role checkbox", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    const checkboxes = screen.getAllByRole("checkbox");
    const viewerCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("Viewer");
    })!;
    expect(viewerCheckbox).not.toBeChecked();
    await user.click(viewerCheckbox);
    expect(viewerCheckbox).toBeChecked();
  });

  it("shows role permissions in each role entry", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Admin")).toBeInTheDocument();
    });
    // Admin role has contracts:read, contracts:write, users:read
    expect(screen.getByText(/contracts:read, contracts:write, users:read/)).toBeInTheDocument();
  });

  it("shows members for existing group", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Members" })).toBeInTheDocument();
    expect(screen.getByText("admin")).toBeInTheDocument();
    // "regular" user is in g2, not g1
    expect(screen.queryByText("regular")).not.toBeInTheDocument();
  });

  it("does not show members section for new group", async () => {
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "New Group" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: "Members" })).not.toBeInTheDocument();
  });

  it("shows effective permissions", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Effective Permissions" })).toBeInTheDocument();
    // Admin role (r1) has p1, p2, p3
    expect(screen.getByText("contracts:read")).toBeInTheDocument();
    expect(screen.getByText("contracts:write")).toBeInTheDocument();
    expect(screen.getByText("users:read")).toBeInTheDocument();
  });

  it("shows empty effective permissions when no roles selected", async () => {
    vi.mocked(rbacApi.getGroup).mockResolvedValue({
      ...mockGroup,
      role_ids: [],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByText("No permissions resolved from selected roles.")).toBeInTheDocument();
  });

  it("updates effective permissions when toggling roles", async () => {
    vi.mocked(rbacApi.getGroup).mockResolvedValue({
      ...mockGroup,
      role_ids: [],
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByText("No permissions resolved from selected roles.")).toBeInTheDocument();

    // Toggle the Viewer role (r2: has p1 = contracts:read)
    const checkboxes = screen.getAllByRole("checkbox");
    const viewerCheckbox = checkboxes.find((cb) => {
      const label = cb.closest("label");
      return label?.textContent?.includes("Viewer");
    })!;
    await user.click(viewerCheckbox);

    // Now contracts:read should appear as effective permission
    const effectiveSection = screen.getByRole("heading", { name: "Effective Permissions" }).parentElement!;
    expect(effectiveSection).toHaveTextContent("contracts:read");
  });

  it("saves updated group", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updateGroup).mockResolvedValue({
      ...mockGroup,
      description: "Updated description",
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    const descInput = screen.getByLabelText("Description");
    await user.clear(descInput);
    await user.type(descInput, "Updated description");
    await user.click(screen.getByText("Save Changes"));
    await waitFor(() => {
      expect(rbacApi.updateGroup).toHaveBeenCalledWith("g1", {
        name: "Admins",
        description: "Updated description",
        role_ids: ["r1"],
        auto_assign_apps: [],
      });
    });
  });

  it("creates new group", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.createGroup).mockResolvedValue({
      _id: "g-new",
      name: "New Group",
      description: "A new group",
      role_ids: [],
      auto_assign_apps: [],
    });
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("Name")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("Name"), "New Group");
    await user.type(screen.getByLabelText("Description"), "A new group");
    await user.click(screen.getByText("Create Group"));
    await waitFor(() => {
      expect(rbacApi.createGroup).toHaveBeenCalledWith({
        name: "New Group",
        description: "A new group",
        role_ids: [],
        auto_assign_apps: [],
      });
    });
  });

  it("shows error when save fails", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.updateGroup).mockRejectedValue(new Error("Save failed"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Save Changes"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Save failed");
    });
  });

  it("has back link to groups list", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Back to groups")).toBeInTheDocument();
  });

  it("has cancel link", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByText("Cancel").closest("a")).toHaveAttribute("href", "/rbac/groups");
  });

  it("shows empty roles state", async () => {
    vi.mocked(rbacApi.listRoles).mockResolvedValue([]);
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByText("No roles available.")).toBeInTheDocument();
    });
  });

  it("shows Application Auto-Assignment section", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Admins")).toBeInTheDocument();
    });
    expect(screen.getByText("Application Auto-Assignment")).toBeInTheDocument();
    expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    expect(screen.getByText("Add")).toBeInTheDocument();
  });

  it("adds app tag via Enter key", async () => {
    const user = userEvent.setup();
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    });
    const input = screen.getByLabelText("App identifier");
    await user.type(input, "hhh-frontend{Enter}");
    expect(screen.getByText("hhh-frontend")).toBeInTheDocument();
    expect(input).toHaveValue("");
  });

  it("adds app tag via Add button", async () => {
    const user = userEvent.setup();
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    });
    const input = screen.getByLabelText("App identifier");
    await user.type(input, "hhh-backoffice");
    await user.click(screen.getByText("Add"));
    expect(screen.getByText("hhh-backoffice")).toBeInTheDocument();
    expect(input).toHaveValue("");
  });

  it("removes app tag", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.getGroup).mockResolvedValue({
      ...mockGroup,
      auto_assign_apps: ["hhh-frontend", "hhh-backoffice"],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("hhh-frontend")).toBeInTheDocument();
    });
    expect(screen.getByText("hhh-backoffice")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Remove hhh-frontend"));
    expect(screen.queryByText("hhh-frontend")).not.toBeInTheDocument();
    expect(screen.getByText("hhh-backoffice")).toBeInTheDocument();
  });

  it("rejects duplicate app identifier", async () => {
    const user = userEvent.setup();
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    });
    const input = screen.getByLabelText("App identifier");
    await user.type(input, "hhh-frontend{Enter}");
    expect(screen.getByText("hhh-frontend")).toBeInTheDocument();
    await user.type(input, "hhh-frontend{Enter}");
    expect(screen.getByText("This app identifier is already added.")).toBeInTheDocument();
  });

  it("rejects invalid app identifier characters", async () => {
    const user = userEvent.setup();
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    });
    const input = screen.getByLabelText("App identifier");
    await user.type(input, "invalid app!{Enter}");
    expect(screen.getByText("Only alphanumeric characters and hyphens are allowed.")).toBeInTheDocument();
  });

  it("does not add empty app identifier", async () => {
    const user = userEvent.setup();
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("App identifier")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Add"));
    expect(screen.queryByText("Only alphanumeric characters and hyphens are allowed.")).not.toBeInTheDocument();
    expect(screen.queryByText("This app identifier is already added.")).not.toBeInTheDocument();
  });

  it("sends auto_assign_apps when creating group", async () => {
    const user = userEvent.setup();
    vi.mocked(rbacApi.createGroup).mockResolvedValue({
      _id: "g-new",
      name: "Test",
      description: "Test group",
      role_ids: [],
      auto_assign_apps: ["my-app"],
    });
    renderPage("new");
    await waitFor(() => {
      expect(screen.getByLabelText("Name")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("Name"), "Test");
    await user.type(screen.getByLabelText("Description"), "Test group");
    await user.type(screen.getByLabelText("App identifier"), "my-app{Enter}");
    await user.click(screen.getByText("Create Group"));
    await waitFor(() => {
      expect(rbacApi.createGroup).toHaveBeenCalledWith({
        name: "Test",
        description: "Test group",
        role_ids: [],
        auto_assign_apps: ["my-app"],
      });
    });
  });

  it("shows existing auto_assign_apps as chips", async () => {
    vi.mocked(rbacApi.getGroup).mockResolvedValue({
      ...mockGroup,
      auto_assign_apps: ["app-one", "app-two"],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("app-one")).toBeInTheDocument();
    });
    expect(screen.getByText("app-two")).toBeInTheDocument();
    expect(screen.getByLabelText("Remove app-one")).toBeInTheDocument();
    expect(screen.getByLabelText("Remove app-two")).toBeInTheDocument();
  });
});
