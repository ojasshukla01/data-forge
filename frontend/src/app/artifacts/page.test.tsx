import { render, screen } from "@testing-library/react";
import ArtifactsPage from "./page";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));

describe("Artifacts page", () => {
  it("renders and type filter works", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            artifacts: [{ path: "out.parquet", name: "out.parquet", size: 1000, run_id: "run_1" }],
            runs: [],
          }),
      })
    ) as ReturnType<typeof fetch>;
    render(<ArtifactsPage />);
    await screen.findByText("out.parquet");
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText(/Showing 1 of 1 artifact/i)).toBeInTheDocument();
  });
});
