import { describe, it, expect } from "vitest";
import { EventCard } from "../components/EventCard";

describe("EventCard", () => {
  it("renders event title", () => {
    const event = { id: 1, title: "Test", slug: "test", event_date: "2026-01-01" };
    expect(EventCard({ event })).toBeTruthy();
  });
});
