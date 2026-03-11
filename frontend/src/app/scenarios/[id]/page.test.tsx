import { render, screen, waitFor } from "@testing-library/react";
import ScenarioDetailPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "scenario_abc123" }),
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Scenario detail page", () => {
  it("renders metadata and masked credential warning when present", async () => {
    global.fetch = vi.fn((url: string | URL) => {
      const u = typeof url === "string" ? url : url.toString();
      if (u.includes("/api/runs")) return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
      if (u.includes("/versions") && !/\/versions\/\d+$/.test(u)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ scenario_id: "scenario_abc123", versions: [], current_version: 1 }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "scenario_abc123",
            name: "Test scenario",
            description: "A test",
            category: "custom",
            tags: ["demo"],
            config: {},
            has_masked_sensitive_fields: true,
            masked_fields: ["db_uri"],
          }),
      });
    }) as ReturnType<typeof fetch>;
    render(<ScenarioDetailPage />);
    await waitFor(() => screen.getByText("Test scenario"));
    expect(screen.getByText(/Some sensitive connection values were not preserved/)).toBeInTheDocument();
  });

  it("renders edit metadata and save/cancel when edit mode opens", async () => {
    global.fetch = vi.fn((url: string | URL) => {
      const u = typeof url === "string" ? url : url.toString();
      if (u.includes("/api/runs")) return Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) });
      if (u.includes("/versions") && !/\/versions\/\d+$/.test(u)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ scenario_id: "scenario_abc123", versions: [], current_version: 1 }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "scenario_abc123",
            name: "Test",
            category: "custom",
            config: {},
          }),
      });
    }) as ReturnType<typeof fetch>;
    render(<ScenarioDetailPage />);
    await waitFor(() => screen.getByText("Test"));
    const editBtn = screen.getByRole("button", { name: /Edit metadata/i });
    editBtn.click();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /^Save$/i })).toBeInTheDocument();
    });
    const cancelButtons = screen.getAllByRole("button", { name: /Cancel/ });
    expect(cancelButtons.length).toBeGreaterThanOrEqual(1);
  });
});
