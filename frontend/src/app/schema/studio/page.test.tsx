import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SchemaStudioPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Schema Studio page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.endsWith("/api/custom-schemas") && (init?.method === "GET" || !init?.method)) {
        return Promise.resolve({
          ok: true,
          json: async () => ([]),
        } as Response);
      }

      if (url.endsWith("/api/custom-schemas") && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: "schema_1", name: "Test", version: 1, schema: {} }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response);
    }) as typeof fetch;
  });

  it("renders studio and allows creating a blank schema client-side", async () => {
    render(<SchemaStudioPage />);

    await screen.findByText("Schema Studio");

    const newButton = screen.getByRole("button", { name: /New schema/i });
    fireEvent.click(newButton);

    await screen.findByText(/Schema editor/);

    const saveButton = screen.getByRole("button", { name: /Save schema/i });
    expect(saveButton).toBeInTheDocument();

    // Saving triggers a POST to the API
    fireEvent.click(saveButton);
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/custom-schemas"),
        expect.any(Object),
      ),
    );
  });

  it("round-trips unique_constraints and check constraint in save payload", async () => {
    render(<SchemaStudioPage />);
    await screen.findByText("Schema Studio");

    fireEvent.click(screen.getByRole("button", { name: /New schema/i }));
    await screen.findByText(/Schema editor \(form mode\)/i);

    // Add table (Tables tab) — then switch stays on Columns; go back to Tables to edit unique constraints
    fireEvent.click(screen.getByRole("button", { name: /Add table/i }));
    fireEvent.click(screen.getByRole("button", { name: /^Tables$/i }));

    // Set unique constraints: one line "email" (use full label text so we match the form label, not the How it works copy)
    const uniqueLabel = screen.getByText("Unique constraints (one per line, comma-separated columns)");
    const uniqueTextarea = uniqueLabel.parentElement?.querySelector("textarea");
    expect(uniqueTextarea).toBeInTheDocument();
    fireEvent.change(uniqueTextarea!, { target: { value: "email" } });

    // Columns tab, add column, set check constraint
    fireEvent.click(screen.getByRole("button", { name: /^Columns$/i }));
    fireEvent.click(screen.getByRole("button", { name: "Add column" }));

    const checkLabel = screen.getByText("Check constraint");
    const checkInput = checkLabel.parentElement?.querySelector("input");
    expect(checkInput).toBeInTheDocument();
    fireEvent.change(checkInput!, { target: { value: "amount >= 0" } });

    // Save
    fireEvent.click(screen.getByRole("button", { name: /Save schema/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/custom-schemas"),
        expect.objectContaining({
          method: "POST",
          body: expect.any(String),
        }),
      );
    });

    const call = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.find(
      (c: [string, RequestInit]) => String(c[0]).endsWith("/api/custom-schemas") && c[1]?.method === "POST",
    );
    const body = call ? JSON.parse((call[1] as RequestInit).body as string) : null;
    expect(body).not.toBeNull();
    expect(body.schema?.tables).toBeDefined();
    expect(Array.isArray(body.schema.tables)).toBe(true);
    expect(body.schema.tables.length).toBeGreaterThanOrEqual(1);
    const table = body.schema.tables[0];
    expect(table.unique_constraints).toEqual([["email"]]);
    expect(table.columns?.length).toBeGreaterThanOrEqual(1);
    expect(table.columns[0].check).toBe("amount >= 0");
  });
});

