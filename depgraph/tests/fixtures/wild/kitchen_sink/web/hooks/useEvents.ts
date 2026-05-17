import { useState, useEffect } from "react";

interface Event {
  id: number;
  title: string;
  slug: string;
  event_date: string;
}

export function useEvents() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/events")
      .then((r) => r.json())
      .then((data) => {
        setEvents(data);
        setLoading(false);
      });
  }, []);

  return { events, loading };
}
