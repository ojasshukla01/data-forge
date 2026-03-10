import { render, screen } from "@testing-library/react";
import HomePage from "./page";

describe("Home page", () => {
  beforeEach(() => {
    global.fetch = vi.fn((url: string) => {
      if (url.includes("/api/runs")) return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
      if (url.includes("/api/scenarios")) return Promise.resolve({ ok: true, json: () => Promise.resolve({ scenarios: [] }) });
      return Promise.reject(new Error("Unknown URL"));
    }) as typeof fetch;
  });

  it("renders hero and main CTA", async () => {
    render(<HomePage />);
    await screen.findByRole("heading", { name: /Data Forge/i });
    expect(screen.getByText(/Schema-aware synthetic data/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Create dataset/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View runs/i })).toBeInTheDocument();
  });
});
