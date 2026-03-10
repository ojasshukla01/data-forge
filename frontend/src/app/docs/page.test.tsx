import { render, screen } from "@testing-library/react";
import DocsPage from "./page";

describe("Docs page", () => {
  it("renders documentation sections", () => {
    render(<DocsPage />);
    expect(screen.getByText("Documentation")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Quick start/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Runs\b/ })).toBeInTheDocument();
    expect(screen.getByLabelText("Documentation index")).toBeInTheDocument();
  });
});
