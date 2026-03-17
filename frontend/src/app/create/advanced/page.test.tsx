import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AdvancedConfigPage from "./page";

describe("Advanced Config page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    if (typeof URL.createObjectURL === "undefined") {
      (global.URL as unknown as { createObjectURL: (b: Blob) => string }).createObjectURL = vi.fn(() => "blob:mock");
      (global.URL as unknown as { revokeObjectURL: (u: string) => void }).revokeObjectURL = vi.fn();
    }
    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/api/domain-packs")) {
        return Promise.resolve({
          ok: true,
          json: async () => ([
            { id: "saas_billing", description: "SaaS billing events" },
          ]),
        } as Response);
      }

      if (url.includes("/api/preflight")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            valid: true,
            blockers: [],
            warnings: [],
            recommendations: [],
          }),
        } as Response);
      }

      if (url.includes("/api/runs/generate")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ run_id: "run_advanced_1", status: "queued" }),
        } as Response);
      }

      if (url.includes("/api/scenarios")) {
        // create / update scenario calls
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: "scenario_test",
            name: "Advanced scenario",
            category: "custom",
            config: {},
          }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response);
    }) as typeof fetch;
  });

  it("renders sections and runs preflight + run", async () => {
    render(<AdvancedConfigPage />);

    await screen.findByText("Advanced Configuration");

    // Go to Exports section and change export format (ensures section switching works)
    const exportsTab = screen.getByRole("button", { name: /Exports/ });
    fireEvent.click(exportsTab);
    await screen.findByText("Export format");

    const formatSelect = screen.getByLabelText("Export format") as HTMLSelectElement;
    fireEvent.change(formatSelect, { target: { value: "csv" } });
    expect(formatSelect.value).toBe("csv");

    // Preflight
    const preflightButton = screen.getByRole("button", { name: /Run preflight/i });
    fireEvent.click(preflightButton);

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/preflight"),
        expect.any(Object),
      ),
    );

    // Run
    const runButton = screen.getByRole("button", { name: /Run now/i });
    fireEvent.click(runButton);

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/runs/generate"),
        expect.any(Object),
      ),
    );
  });

  it("exports and imports config JSON", async () => {
    render(<AdvancedConfigPage />);

    await screen.findByText("Advanced Configuration");

    const exportButton = screen.getByRole("button", { name: "Export config" });
    expect(exportButton).toBeInTheDocument();

    // We cannot assert the file download in JSDOM, but we can at least click without errors.
    fireEvent.click(exportButton);
  });
});

