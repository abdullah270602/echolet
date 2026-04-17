const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export interface DemoSession {
  token: string;
  livekit_url: string;
  room_name: string;
  max_seconds: number;
}

export class DemoError extends Error {}

export async function createDemoSession(): Promise<DemoSession> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/demo/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
  } catch {
    throw new DemoError('Could not reach the demo server. Check your connection and try again.');
  }

  // 429 = rate limited or daily budget used up, 503 = demo not configured
  if (response.status === 429 || response.status === 503) {
    const body = await response.json().catch(() => null);
    throw new DemoError(body?.detail || 'The live demo is not available right now.');
  }
  if (!response.ok) {
    throw new DemoError('The demo could not start. Try again in a moment.');
  }
  return response.json();
}
