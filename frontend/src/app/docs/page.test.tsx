import { render, screen } from "@testing-library/react";
import DocsPage from "./page";

describe("Docs page", () => {
  it("renders documentation sections", () => {
    render(<DocsPage />);
    expect(screen.getByText("Documentation")).toBeInTheDocument();
    expect(screen.getByText(/Quick start/)).toBeInTheDocument();
    expect(screen.getByText(/Understanding runs/)).toBeInTheDocument();
  });
});
