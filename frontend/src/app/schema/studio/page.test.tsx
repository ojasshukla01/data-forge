import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SchemaStudioPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
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

      if (url.includes("/api/custom-schemas/validate") && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ valid: true, errors: [], warnings: [] }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      } as Response);
    }) as typeof fetch;
  });

  it("renders studio and allows creating a blank schema client-side", async () => {
    const user = userEvent.setup();
    render(<SchemaStudioPage />);

    await screen.findByText("Schema Studio");

    const newButton = screen.getByRole("button", { name: /New schema/i });
    await user.click(newButton);

    await screen.findByText(/Visual schema designer|Schema editor/);

    const saveButton = screen.getByRole("button", { name: /Save schema|^Save$/i });
    expect(saveButton).toBeInTheDocument();

    await user.click(saveButton);
    await waitFor(() => {
      const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls;
      const hasCustomSchemasCall = calls.some(
        (c: [string, RequestInit?]) => String(c[0]).includes("/api/custom-schemas"),
      );
      expect(hasCustomSchemasCall).toBe(true);
    });
  });

  it("adds table, saves, and shows success (userEvent for realistic async interactions)", async () => {
    const user = userEvent.setup();
    render(<SchemaStudioPage />);
    await screen.findByText("Schema Studio");

    await user.click(screen.getByRole("button", { name: /New schema/i }));
    await screen.findByText(/Visual schema designer|Schema editor/);

    await user.click(screen.getByRole("button", { name: /^Form$/i }));
    const addTableBtn = screen.getByRole("button", { name: /Add table/i });
    expect(addTableBtn).toBeInTheDocument();

    await user.click(addTableBtn);
    await waitFor(() => expect(screen.getByText("table_1")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /Save schema/i }));

    await waitFor(() => expect(screen.getByText(/Schema saved successfully/i)).toBeInTheDocument());
    const createCalls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.filter(
      (c: [string, RequestInit]) => {
        const url = String(c[0]);
        return url.includes("/api/custom-schemas") && !url.includes("/validate") && c[1]?.method === "POST";
      },
    );
    expect(createCalls.length).toBeGreaterThan(0);
  });
});

