// =============================================================================
// api/settings.ts — User settings and Google Drive API service
// Settings include language/dark-mode preferences and optional Google account
// integration for generating signature print sheets via Google Sheets API.
// =============================================================================

import { api } from '@/api/client'
import type { Settings } from '@/types'

// Google connection status returned by GET /settings/google
interface GoogleStatus {
  connected: boolean
  google_email: string | null
  drive_used_bytes: number | null
  drive_total_bytes: number | null
}

// Signature print file metadata
interface SignaturePrintFile {
  id: string
  order_id: string
  sheet_url: string
  created_at: string
}

export const settingsApi = {
  // GET /settings — current user's language + dark mode preferences
  get: () =>
    api.get<Settings>('/settings'),

  // PUT /settings — save language/dark-mode changes
  update: (body: Partial<Pick<Settings, 'language' | 'dark_mode'>>) =>
    api.put<Settings>('/settings', body),

  // GET /settings/google — check if Google account is connected + storage info
  getGoogle: () =>
    api.get<GoogleStatus>('/settings/google'),

  // POST /settings/google/connect — store Google OAuth token
  connectGoogle: (token: string) =>
    api.post<void>('/settings/google/connect', { token }),

  // DELETE /settings/google/disconnect — revoke Google account link
  disconnectGoogle: () =>
    api.delete<void>('/settings/google/disconnect'),

  // POST /settings/google/test-connection — verify OAuth token is still valid
  testGoogleConnection: () =>
    api.post<{ ok: boolean }>('/settings/google/test-connection', {}),

  // POST /signature-print/generate — create a Google Sheet for an order
  generateSignaturePrint: (orderId: string) =>
    api.post<SignaturePrintFile>('/signature-print/generate', { order_id: orderId }),

  // GET /signature-print/list — list previously generated signature sheets
  listSignaturePrints: () =>
    api.get<SignaturePrintFile[]>('/signature-print/list'),
}
