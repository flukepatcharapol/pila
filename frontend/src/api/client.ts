/**
 * client.ts — Fetch-based API client with auth error handling
 *
 * Handles 401 responses from protected routes per design doc § 8.3:
 *   - session_expired / session_revoked → clearAllTokens + showSessionExpiredModal
 *   - access JWT expired, password session still valid → redirect to /pin
 *   - access JWT expired, password session also gone  → clearAllTokens + redirect to /login
 *
 * Design doc: docs/auth_dual_session_design.md § 8
 */

import {
  clearAllTokens,
  getAccessToken,
  isPasswordSessionValid,
} from '@/lib/auth';

/** Shape of error JSON returned by the API on 4xx responses. */
export interface ApiErrorBody {
  error_code?: string;
  detail?: string;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly errorCode: string | undefined,
    public readonly detail: string | undefined,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Callback invoked when the password session has expired or been revoked.
 * Set this before making API calls (e.g. in main.tsx or a router guard).
 */
let _onSessionExpired: (() => void) | null = null;

export function setSessionExpiredHandler(handler: () => void): void {
  _onSessionExpired = handler;
}

/**
 * React-router navigate function injected at app startup.
 * We use a reference so the API client doesn't import the router directly.
 */
let _navigate: ((path: string) => void) | null = null;

export function setNavigate(navigate: (path: string) => void): void {
  _navigate = navigate;
}

function navigate(path: string): void {
  if (_navigate) {
    _navigate(path);
  } else {
    window.location.href = path;
  }
}

function showSessionExpiredModal(): void {
  if (_onSessionExpired) {
    _onSessionExpired();
  } else {
    // Fallback when handler not registered yet (e.g. during early boot)
    clearAllTokens();
    navigate('/login');
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  /** Skip attaching the Authorization: Bearer <access_token> header. */
  skipAuth?: boolean;
}

async function request<T>(
  method: string,
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, skipAuth = false, headers: extraHeaders = {}, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extraHeaders as Record<string, string>),
  };

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  });

  if (response.ok) {
    // 204 No Content — return empty object
    if (response.status === 204) return {} as T;
    return response.json() as Promise<T>;
  }

  // Parse error body (best-effort)
  let errorBody: ApiErrorBody = {};
  try {
    errorBody = (await response.json()) as ApiErrorBody;
  } catch {
    // non-JSON error body — ignore
  }

  // --- 401 handling (design doc § 8.3) ---
  if (response.status === 401) {
    const errorCode = errorBody.error_code;

    if (errorCode === 'session_expired' || errorCode === 'session_revoked') {
      // Password session expired server-side → must log in again
      clearAllTokens();
      showSessionExpiredModal();
      throw new ApiError(401, errorCode, errorBody.detail, errorBody.detail ?? 'Session expired');
    }

    // Access JWT expired — decide redirect based on local password session state
    if (isPasswordSessionValid()) {
      navigate('/pin');
    } else {
      clearAllTokens();
      navigate('/login');
    }

    throw new ApiError(401, errorCode, errorBody.detail, errorBody.detail ?? 'Unauthorized');
  }

  throw new ApiError(
    response.status,
    errorBody.error_code,
    errorBody.detail,
    errorBody.detail ?? `HTTP ${response.status}`
  );
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------

export const api = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>('GET', path, options);
  },
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('POST', path, { ...options, body });
  },
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PUT', path, { ...options, body });
  },
  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PATCH', path, { ...options, body });
  },
  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>('DELETE', path, options);
  },
};
