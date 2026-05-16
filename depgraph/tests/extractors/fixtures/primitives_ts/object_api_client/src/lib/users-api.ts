export const usersApi = {
  fetch(id: string) { return id; },
  create: (name: string) => ({ name }),
  endpoint: "/users",
};
