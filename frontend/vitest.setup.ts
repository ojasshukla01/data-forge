import "@testing-library/jest-dom";
import "vitest-location-mock";
import { vi } from "vitest";

// Suppress jsdom "Not implemented: navigation" when anchor.click() triggers download
HTMLAnchorElement.prototype.click = vi.fn();

// ResizeObserver (required by ReactFlow in Schema Studio)
global.ResizeObserver = class ResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
};

// Mock Next.js router
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));
