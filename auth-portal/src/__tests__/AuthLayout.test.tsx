import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import AuthLayout from "@/layouts/AuthLayout";

describe("AuthLayout", () => {
  it("renders the Hexadian logo image", () => {
    render(<AuthLayout>content</AuthLayout>);
    const logo = screen.getByAltText("Hexadian");
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute("src", "/brand/HEXADIAN-Letters.png");
  });

  it("renders the Authentication Portal subtitle", () => {
    render(<AuthLayout>content</AuthLayout>);
    expect(screen.getByText("Hexadian Authentication Portal")).toBeInTheDocument();
  });

  it("renders children inside the card", () => {
    render(<AuthLayout><span data-testid="child">test child</span></AuthLayout>);
    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(screen.getByText("test child")).toBeInTheDocument();
  });

  it("renders the background image container", () => {
    const { container } = render(<AuthLayout>content</AuthLayout>);
    const outer = container.firstElementChild as HTMLElement;
    expect(outer.style.backgroundImage).toContain(
      "HEXADIAN-Background.png",
    );
  });

  it("renders the dark overlay for readability", () => {
    const { container } = render(<AuthLayout>content</AuthLayout>);
    const overlay = container.querySelector("[aria-hidden='true']");
    expect(overlay).toBeInTheDocument();
    expect(overlay).toHaveClass("bg-black/85");
  });
});
