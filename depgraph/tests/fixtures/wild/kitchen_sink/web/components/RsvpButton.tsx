import React, { useState } from "react";
import { useCurrentUser } from "../hooks/useCurrentUser";

interface RsvpButtonProps {
  eventId: number;
}

export function RsvpButton({ eventId }: RsvpButtonProps) {
  const [submitted, setSubmitted] = useState(false);
  const { user } = useCurrentUser();

  function handleClick() {
    setSubmitted(true);
  }

  if (submitted) {
    return <span>RSVP sent!</span>;
  }

  return (
    <button onClick={handleClick} disabled={!user}>
      RSVP
    </button>
  );
}
