import React from "react";
import { RsvpButton } from "./RsvpButton";

interface Event {
  id: number;
  title: string;
  slug: string;
  event_date: string;
}

interface EventCardProps {
  event: Event;
}

export function EventCard({ event }: EventCardProps) {
  return (
    <div className="event-card">
      <h2>{event.title}</h2>
      <p>{event.event_date}</p>
      <RsvpButton eventId={event.id} />
    </div>
  );
}
