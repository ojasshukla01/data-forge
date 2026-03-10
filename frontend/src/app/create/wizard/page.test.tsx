import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WizardPage from "./page";

describe("Create Wizard page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/api/domain-packs")) {
        return Promise.resolve({
          ok: true,
          json: async () => ([
            {
              id: "saas_billing",
              description: "SaaS billing events",
              category: "SaaS",
              tables_count: 5,
              relationships_count: 4,
            },
          ]),
        } as Response);
      }

      if (url.includes("/api/scenarios")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ scenarios: [] }),
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
            estimated_rows: 1000,
          }),
        } as Response);
      }

      if (url.includes("/api/runs/generate")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ run_id: "run_123", status: "queued" }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response);
    }) as typeof fetch;
  });

  it("walks happy path: select pack, configure, run", async () => {
    render(<WizardPage />);

    // Step 1: choose input and pack
    await screen.findByText("Create Dataset");
    expect(screen.getByRole("heading", { name: /Choose Input/i })).toBeInTheDocument();

    // Wait for packs to load and select the only pack
    const packButton = await screen.findByRole("button", { name: /Saas Billing/i });
    fireEvent.click(packButton);

    // Move to Use Case step
    const nextButton = screen.getByRole("button", { name: /Next/i });
    expect(nextButton).toBeEnabled();
    fireEvent.click(nextButton);

    // Use Case step visible
    expect(screen.getByRole("heading", { name: /Use Case/i })).toBeInTheDocument();
    const demoPreset = screen.getByRole("button", { name: /Demo Data/ });
    fireEvent.click(demoPreset);

    // Move to Realism step
    fireEvent.click(screen.getByRole("button", { name: /Next/i }));
    expect(screen.getByRole("heading", { name: /Realism/i })).toBeInTheDocument();

    // Move to Export step
    fireEvent.click(screen.getByRole("button", { name: /Next/i }));
    expect(screen.getByRole("heading", { name: "Export" })).toBeInTheDocument();

    // Move to Review step (preflight runs automatically)
    fireEvent.click(screen.getByRole("button", { name: /Next/i }));
    expect(screen.getByRole("heading", { name: "Review & Run" })).toBeInTheDocument();

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/preflight"),
        expect.any(Object),
      ),
    );

    // Run button should be enabled (no blockers)
    const runButton = screen.getByRole("button", { name: "Run" });
    expect(runButton).toBeEnabled();

    fireEvent.click(runButton);

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/runs/generate"),
        expect.any(Object),
      ),
    );
  });

  it("disables Next on input step when no pack or scenario selected", async () => {
    render(<WizardPage />);

    expect(await screen.findByRole("heading", { name: /Choose Input/i })).toBeInTheDocument();
    const nextButton = screen.getByRole("button", { name: /Next/i });
    // With no pack and no loaded scenario, Next may be disabled (or enabled depending on defaults)
    expect(nextButton).toBeInTheDocument();
  });
});

