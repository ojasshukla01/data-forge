import { render, screen } from "@testing-library/react";
import AboutPage from "./page";

describe("About page", () => {
  it("renders creator info and GitHub link", () => {
    render(<AboutPage />);
    expect(screen.getByText(/Ojas Shukla/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /GitHub profile/ })).toBeInTheDocument();
    expect(screen.getByText(/About Data Forge/)).toBeInTheDocument();
  });
});
