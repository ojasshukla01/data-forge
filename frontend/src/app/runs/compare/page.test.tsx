import { render, screen } from "@testing-library/react";
import ComparePage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({}),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

describe("Compare runs page", () => {
  it("renders compare title and run selectors", async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ runs: [] }) })) as ReturnType<typeof fetch>;
    render(<ComparePage />);
    expect(screen.getByText("Compare runs")).toBeInTheDocument();
  });
});
