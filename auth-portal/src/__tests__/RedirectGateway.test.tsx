import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RedirectGateway from "@/pages/RedirectGateway";

vi.mock("@/lib/auth", () => ({
  parseAccessToken: vi.fn(),
}));

vi.mock("@/api/settings", () => ({
  getPortalRedirect: vi.fn(),
}));

import { parseAccessToken } from "@/lib/auth";
import { getPortalRedirect } from "@/api/settings";
const mockParseAccessToken = vi.mocked(parseAccessToken);
const mockGetPortalRedirect = vi.mocked(getPortalRedirect);

function renderGateway(initialEntries?: string[]) {
  return render(
    <MemoryRouter initialEntries={initialEntries ?? ["/unknown"]}>
      <Routes>
        <Route path="/login" element={<div>login page</div>} />
        <Route path="/verify" element={<div>verify page</div>} />
        <Route path="*" element={<RedirectGateway />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RedirectGateway", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "http://localhost/" },
    });
  });

  it("redirects to /login when not authenticated", () => {
    mockParseAccessToken.mockReturnValue(null);
    renderGateway();

    expect(screen.getByText("login page")).toBeInTheDocument();
    expect(mockGetPortalRedirect).not.toHaveBeenCalled();
  });

  it("redirects to /verify when authenticated but not verified", () => {
    mockParseAccessToken.mockReturnValue({
      userId: "user-1",
      username: "testuser",
      groups: [],
      roles: [],
      permissions: [],
      rsiHandle: "test-handle",
      rsiVerified: false,
    });
    renderGateway();

    expect(screen.getByText("verify page")).toBeInTheDocument();
    expect(mockGetPortalRedirect).not.toHaveBeenCalled();
  });

  it("fetches portal settings and redirects when authenticated and verified", async () => {
    mockParseAccessToken.mockReturnValue({
      userId: "user-1",
      username: "testuser",
      groups: [],
      roles: [],
      permissions: [],
      rsiHandle: "test-handle",
      rsiVerified: true,
    });
    mockGetPortalRedirect.mockResolvedValueOnce({
      default_redirect_url: "https://portal.hexadian.com",
    });

    renderGateway();

    await waitFor(() => {
      expect(mockGetPortalRedirect).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(window.location.href).toBe("https://portal.hexadian.com");
    });
  });
});
