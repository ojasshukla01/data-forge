import { render, screen, waitFor } from "@testing-library/react";
import ScenariosPage from "./page";

const mockFetch = (data: unknown) => {
  global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(data) })) as ReturnType<typeof fetch>;
};

describe("Scenarios page", () => {
  it("renders title and empty state when no scenarios", async () => {
    mockFetch({ scenarios: [] });
    render(<ScenariosPage />);
    expect(screen.getByText("Scenario library")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/No scenarios yet/)).toBeInTheDocument();
    });
  });

  it("renders scenario cards when scenarios exist", async () => {
    mockFetch({
      scenarios: [
        { id: "s1", name: "Test scenario", category: "custom", source_pack: "ecommerce" },
      ],
    });
    render(<ScenariosPage />);
    await waitFor(() => {
      expect(screen.getByText("Test scenario")).toBeInTheDocument();
    });
  });

  it("renders Start in wizard and Edit in Advanced actions", async () => {
    mockFetch({
      scenarios: [
        { id: "s1", name: "Test scenario", category: "custom", source_pack: "ecommerce" },
      ],
    });
    render(<ScenariosPage />);
    await waitFor(() => {
      expect(screen.getByText("Test scenario")).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /Start in wizard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Edit in Advanced/i })).toBeInTheDocument();
  });
});
