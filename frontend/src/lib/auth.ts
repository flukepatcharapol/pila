/**
 * auth.ts — Session storage helpers for dual-session auth (Approach B)
 *
 * Two-layer session:
 *   - Password session (opaque token, 30 days): stored in localStorage
 *   - Access session (JWT, 6 hours): stored in localStorage
 *
 * Design doc: docs/auth_dual_session_design.md § 8
 */

const KEYS = {
  PASSWORD_SESSION_TOKEN: 'password_session_token',
  PASSWORD_SESSION_EXPIRES_AT: 'password_session_expires_at',
  ACCESS_TOKEN: 'access_token',
} as const;

/**
 * Store the opaque password session token received after login.
 * @param token - opaque password_session_token (or temporary_token) from POST /auth/login
 * @param expiresIn - seconds until the password session expires
 */
export function storePasswordSession(token: string, expiresIn: number): void {
  const expiresAt = Date.now() + expiresIn * 1000;
  localStorage.setItem(KEYS.PASSWORD_SESSION_TOKEN, token);
  localStorage.setItem(KEYS.PASSWORD_SESSION_EXPIRES_AT, String(expiresAt));
}

/**
 * Store the JWT access token received after a successful PIN verify.
 * @param jwt - access_token from POST /auth/pin/verify
 */
export function storeAccessToken(jwt: string): void {
  localStorage.setItem(KEYS.ACCESS_TOKEN, jwt);
}

/**
 * Remove all auth tokens from storage (logout / session expired).
 */
export function clearAllTokens(): void {
  localStorage.removeItem(KEYS.PASSWORD_SESSION_TOKEN);
  localStorage.removeItem(KEYS.PASSWORD_SESSION_EXPIRES_AT);
  localStorage.removeItem(KEYS.ACCESS_TOKEN);
}

/**
 * Return true if a password session token exists and has not expired locally.
 * Does NOT verify the token against the server.
 */
export function isPasswordSessionValid(): boolean {
  const expiresAt = Number(localStorage.getItem(KEYS.PASSWORD_SESSION_EXPIRES_AT));
  if (!expiresAt) return false;
  return Date.now() < expiresAt;
}

/**
 * Return the stored opaque password session token, or null if absent.
 */
export function getPasswordSessionToken(): string | null {
  return localStorage.getItem(KEYS.PASSWORD_SESSION_TOKEN);
}

/**
 * Return the stored JWT access token, or null if absent.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(KEYS.ACCESS_TOKEN);
}
