import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SchemaStudioPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Schema Studio page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.endsWith("/api/custom-schemas")) {
        return Promise.resolve({
          ok: true,
          json: async () => ([]),
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
});

