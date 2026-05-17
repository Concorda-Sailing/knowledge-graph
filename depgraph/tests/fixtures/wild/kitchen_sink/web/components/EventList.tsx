import React from "react";
import { useEvents } from "../hooks/useEvents";
import { EventCard } from "./EventCard";

export function EventList() {
  const { events, loading } = useEvents();

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="event-list">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
