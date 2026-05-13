// Sample JS code the extractor must handle.

const API_BASE_URL = 'https://api.example.com';

export async function getHealth() {
  const r = await fetch(`${API_BASE_URL}/health`);
  return r.json();
}

export async function importEvent(id: string, payload: unknown) {
  return fetch(`${API_BASE_URL}/api/events/${id}/import`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listOrgs() {
  return fetch('/api/organizations', { method: 'GET' });
}

// Should be SKIPPED — first arg is a bare variable, can't resolve.
async function dynamic(url: string) {
  return fetch(url);
}
