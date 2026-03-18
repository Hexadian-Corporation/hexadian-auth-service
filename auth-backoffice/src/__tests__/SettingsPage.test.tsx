import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import SettingsPage from "@/pages/SettingsPage";

vi.mock("@/api/settings", () => ({
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
}));

import * as settingsApi from "@/api/settings";

function renderPage() {
  const router = createMemoryRouter(
    [{ path: "/settings", element: <SettingsPage /> }],
    { initialEntries: ["/settings"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(settingsApi.getSettings).mockResolvedValue({
      default_redirect_url: "https://example.com",
    });
  });

  it("renders the settings form with current value", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Default redirect URL")).toHaveValue("https://example.com");
    });
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(settingsApi.getSettings).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Loading settings…")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    vi.mocked(settingsApi.getSettings).mockRejectedValue(new Error("Network error"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("updates settings on submit", async () => {
    const user = userEvent.setup();
    vi.mocked(settingsApi.updateSettings).mockResolvedValue({
      default_redirect_url: "https://new.example.com",
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Default redirect URL")).toBeInTheDocument();
    });
    const input = screen.getByLabelText("Default redirect URL");
    await user.clear(input);
    await user.type(input, "https://new.example.com");
    await user.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(settingsApi.updateSettings).toHaveBeenCalledWith({
        default_redirect_url: "https://new.example.com",
      });
    });
    expect(screen.getByRole("status")).toHaveTextContent("Settings saved successfully.");
  });

  it("shows error on update failure", async () => {
    const user = userEvent.setup();
    vi.mocked(settingsApi.updateSettings).mockRejectedValue(new Error("Save failed"));
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Default redirect URL")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Save failed");
    });
  });

  it("renders page heading", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    });
  });
});
