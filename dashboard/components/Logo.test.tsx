import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Logo } from "./Logo";

describe("Logo", () => {
  it("renders the full wordmark by default", () => {
    render(<Logo />);

    expect(screen.getByRole("img", { name: "Cornerstone Services" })).toBeInTheDocument();
  });

  it("renders the compact mark variant", () => {
    render(<Logo variant="mark" />);

    expect(screen.getByRole("img", { name: "Cornerstone mark" })).toBeInTheDocument();
  });
});
