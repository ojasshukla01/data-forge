import { render, screen } from "@testing-library/react";
import RunDetailPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "run_abc123" }),
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Run detail page", () => {
  it("renders source scenario link when present", async () => {
    global.fetch = vi.fn((url: string) => {
      if (url.includes("/lineage")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(null) });
      }
      if (url.includes("/manifest")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(null) });
      }
      if (url.includes("/timeline")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ run_id: "run_abc123", stages: [], events: [] }) });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "run_abc123",
            status: "succeeded",
            run_type: "generate",
            created_at: Date.now() / 1000,
            config_summary: {},
            source_scenario_id: "scenario_xyz",
            stage_progress: [],
          }),
      });
    }) as ReturnType<typeof fetch>;
    render(<RunDetailPage />);
    await screen.findByText("run_abc123");
    expect(screen.getByRole("link", { name: /scenario_xyz/ })).toBeInTheDocument();
  });

  it("renders custom schema provenance in Config, Lineage, and Manifest", async () => {
    const urlStr = (u: unknown) => (typeof u === "string" ? u : u instanceof Request ? u.url : String(u));
    global.fetch = vi.fn((input: unknown) => {
      const url = urlStr(input);
      if (url.includes("/lineage")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              run_id: "run_abc123",
              schema_source_type: "custom_schema",
              custom_schema_id: "schema_test123",
              custom_schema_version: 2,
            }),
        });
      }
      if (url.includes("/manifest")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              run_id: "run_abc123",
              schema_source_type: "custom_schema",
              custom_schema_id: "schema_test123",
              custom_schema_version: 2,
            }),
        });
      }
      if (url.includes("/timeline")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ run_id: "run_abc123", stages: [], events: [] }) });
      }
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "run_abc123",
            status: "succeeded",
            run_type: "generate",
            config_summary: { custom_schema_id: "schema_test123", custom_schema_version: 2 },
            source_scenario_id: null,
            stage_progress: [],
          }),
      });
    }) as ReturnType<typeof fetch>;
    render(<RunDetailPage />);
    await screen.findByRole("heading", { name: /run_abc123/ });
    // Custom schema ID appears in Config, StatCard, Lineage, and Manifest
    const schemaIds = await screen.findAllByText("schema_test123", {}, { timeout: 3000 });
    expect(schemaIds.length).toBeGreaterThan(0);
    expect(screen.getAllByText("Custom schema").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/v2/).length).toBeGreaterThan(0);
  });
});
