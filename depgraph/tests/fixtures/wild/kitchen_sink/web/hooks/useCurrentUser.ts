import { useState, useEffect } from "react";

interface User {
  id: number;
  email: string;
  display_name: string | null;
}

export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch("/api/users/me")
      .then((r) => r.json())
      .then((data) => setUser(data));
  }, []);

  return { user };
}
