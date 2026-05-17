import { describe, it, expect } from "vitest";
import { useEvents } from "../hooks/useEvents";

describe("useEvents", () => {
  it("returns events and loading state", () => {
    const result = useEvents();
    expect(result.loading).toBe(true);
    expect(result.events).toEqual([]);
  });
});
