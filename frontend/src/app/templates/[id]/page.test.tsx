import { render, screen, waitFor } from "@testing-library/react";
import PackDetailPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "saas_billing" }),
}));

describe("Pack detail template page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/api/domain-packs/saas_billing")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: "saas_billing",
            name: "SaaS Billing",
            description: "SaaS billing domain",
            category: "SaaS",
            tables: [
              { name: "customers", columns: ["id", "email"], primary_key: ["id"] },
            ],
            relationships_count: 1,
            key_entities: ["customer"],
            supported_features: ["etl_simulation"],
            recommended_use_cases: ["Billing tests"],
          }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response);
    }) as typeof fetch;
  });

  it("shows pack details and CTAs into wizard and schema diagram", async () => {
    render(<PackDetailPage />);

    await screen.findByText("SaaS Billing");
    await screen.findByText("SaaS billing domain");
    await screen.findByText(/Tables \(1\)/);
    await screen.findByText(/customers/);

    // CTAs
    const useTemplateCta = screen.getAllByRole("link", { name: /Use This Template/i })[0];
    expect(useTemplateCta.getAttribute("href")).toContain("/create/wizard?pack=saas_billing");

    const schemaDiagramCta = screen.getAllByRole("link", { name: /Schema Diagram/i })[0];
    expect(schemaDiagramCta.getAttribute("href")).toContain("/schema?pack=saas_billing");

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/domain-packs/saas_billing"));
    });
  });
});

