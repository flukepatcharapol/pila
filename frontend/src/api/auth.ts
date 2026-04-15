// =============================================================================
// api/auth.ts — Authentication API service
// Wraps the auth endpoints from the dual-session architecture:
//   password_session_token (opaque, 30 days) + access_token (JWT, 6 hours)
// =============================================================================

import { api } from '@/api/client'
import type { CurrentUser } from '@/types'

export const authApi = {
  // GET /auth/me — fetch the logged-in user's profile (role, branch, display_name)
  // Called by AuthContext on mount to populate the global user state
  me: () =>
    api.get<CurrentUser>('/auth/me'),

  // POST /auth/logout — revoke the current password session server-side
  // The client also clears tokens from localStorage after this call
  logout: () =>
    api.post<void>('/auth/logout', {}),

  // POST /auth/pin/forgot — request a PIN reset OTP sent to the user's email
  pinForgot: (email: string) =>
    api.post<void>('/auth/pin/forgot', { email }, { skipAuth: true }),

  // POST /auth/pin/reset — set a new PIN using the OTP from the email
  pinReset: (email: string, otp: string, new_pin: string) =>
    api.post<void>('/auth/pin/reset', { email, otp, new_pin }, { skipAuth: true }),

  // POST /auth/password/change — change password while logged in
  // Requires both current_password and new_password; also revokes all sessions
  passwordChange: (current_password: string, new_password: string) =>
    api.post<void>('/auth/password/change', { current_password, new_password }),
}
