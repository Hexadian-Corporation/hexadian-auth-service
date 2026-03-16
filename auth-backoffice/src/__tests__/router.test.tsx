import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import DashboardLayout from "@/layouts/DashboardLayout";
import UsersPage from "@/pages/UsersPage";
import LoginPage from "@/pages/LoginPage";

describe("Router", () => {
  it("renders the login page", () => {
    const router = createMemoryRouter(
      [{ path: "/login", element: <LoginPage /> }],
      { initialEntries: ["/login"] },
    );
    render(<RouterProvider router={router} />);
    expect(screen.getByText("Auth Backoffice")).toBeInTheDocument();
  });

  it("renders the users page inside dashboard layout", () => {
    const router = createMemoryRouter(
      [
        {
          path: "/",
          element: <DashboardLayout />,
          children: [{ path: "users", element: <UsersPage /> }],
        },
      ],
      { initialEntries: ["/users"] },
    );
    render(<RouterProvider router={router} />);
    expect(screen.getByRole("heading", { name: "Users" })).toBeInTheDocument();
  });

  it("renders sidebar navigation links", () => {
    const router = createMemoryRouter(
      [
        {
          path: "/",
          element: <DashboardLayout />,
          children: [{ path: "users", element: <UsersPage /> }],
        },
      ],
      { initialEntries: ["/users"] },
    );
    render(<RouterProvider router={router} />);
    expect(screen.getByText("Permissions")).toBeInTheDocument();
    expect(screen.getByText("Roles")).toBeInTheDocument();
    expect(screen.getByText("Groups")).toBeInTheDocument();
  });
});
