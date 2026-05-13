/**
 * Call History API Service
 * Handles all API calls for the Call History feature
 */

import type { CallHistoryItem } from '../types/callHistory';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * API Error class for consistent error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Helper to make authenticated API requests
 */
async function apiRequest<T>(
  endpoint: string,
  getToken: () => Promise<string | null>,
  options: RequestInit = {}
): Promise<T> {
  const token = await getToken();
  if (!token) {
    throw new ApiError('Not authenticated', 401);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const errorData = await response.json();
      detail = errorData.detail;
    } catch {
      // Ignore JSON parse errors
    }

    if (response.status === 401) {
      throw new ApiError('Authentication failed', 401, detail);
    }
    if (response.status === 403) {
      throw new ApiError('Not authorized', 403, detail);
    }
    if (response.status === 404) {
      throw new ApiError('Not found', 404, detail);
    }
    if (response.status === 400) {
      throw new ApiError(detail || 'Bad request', 400, detail);
    }

    throw new ApiError(detail || 'Request failed', response.status, detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * Fetch call history for the current user
 * @param getToken - Function to get auth token from Clerk
 * @param limit - Maximum number of records to fetch (default: 50)
 */
export async function fetchCallHistory(
  getToken: () => Promise<string | null>,
  limit: number = 50
): Promise<CallHistoryItem[]> {
  return apiRequest<CallHistoryItem[]>(
    `/session/history?limit=${limit}`,
    getToken
  );
}

/**
 * Fetch a single call by ID
 * @param id - The call session ID
 * @param getToken - Function to get auth token from Clerk
 */
export async function fetchCallById(
  id: number,
  getToken: () => Promise<string | null>
): Promise<CallHistoryItem> {
  return apiRequest<CallHistoryItem>(
    `/session/${id}`,
    getToken
  );
}
