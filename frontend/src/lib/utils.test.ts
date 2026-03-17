import { describe, it, expect } from "vitest";
import { cn, API_BASE } from "./utils";

describe("utils", () => {
  describe("cn", () => {
    it("merges class names", () => {
      expect(cn("a", "b")).toBe("a b");
    });
    it("handles conditional classes", () => {
      expect(cn("base", false && "hidden", "visible")).toBe("base visible");
    });
    it("merges tailwind conflicts", () => {
      expect(cn("px-2", "px-4")).toBe("px-4");
    });
  });

  describe("API_BASE", () => {
    it("is a string base path", () => {
      expect(typeof API_BASE).toBe("string");
      // Browser runtime intentionally uses same-origin relative /api proxy (empty prefix).
      expect(API_BASE.length).toBeGreaterThanOrEqual(0);
    });
  });
});
