import { render, screen, fireEvent } from "@testing-library/react";
import TemplatesPage from "./page";

const mockTemplates = [
  { id: "saas_billing", name: "SaaS Billing", description: "SaaS billing domain", category: "SaaS", tables_count: 5, relationships_count: 4, key_entities: ["customer", "subscription"] },
  { id: "ecommerce", name: "Ecommerce", description: "Ecommerce transactions", category: "Ecommerce", tables_count: 6, relationships_count: 5, key_entities: ["order", "customer"] },
];

describe("Templates page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/templates/hidden")) {
        return Promise.resolve({ ok: true, json: async () => [] } as Response);
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockTemplates,
      } as Response);
    }) as typeof fetch;
  });

  it("lists templates and supports category filter", async () => {
    render(<TemplatesPage />);

    await screen.findByText("Templates");
    await screen.findByText("SaaS Billing");
    expect(screen.getAllByText("Ecommerce").length).toBeGreaterThan(0);

    const filterSelect = screen.getByRole("combobox") as HTMLSelectElement;

    fireEvent.change(filterSelect, { target: { value: "Ecommerce" } });

    expect(filterSelect.value).toBe("Ecommerce");
  });
});

