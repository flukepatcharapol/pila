// =============================================================================
// api/bookings.ts — Booking / staff schedule API service
// Bookings represent training time slots; flow: pending → confirmed → cancelled.
// Confirming a booking triggers a LINE notification if the customer has LINE ID.
// =============================================================================

import { api } from '@/api/client'
import type { Booking, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const bookingsApi = {
  // GET /bookings — list bookings, filterable by trainer/date/status/branch
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<Booking>>(`/bookings${toQuery(params)}`),

  // GET /bookings/:id — single booking detail
  get: (id: string) =>
    api.get<Booking>(`/bookings/${id}`),

  // POST /bookings — create a new booking (status defaults to "pending")
  create: (body: Partial<Booking>) =>
    api.post<Booking>('/bookings', body),

  // PUT /bookings/:id — update booking fields (time, trainer, notes)
  update: (id: string, body: Partial<Booking>) =>
    api.put<Booking>(`/bookings/${id}`, body),

  // PUT /bookings/:id/confirm — advance status from pending → confirmed
  // BE sends LINE notification if customer has line_id set
  confirm: (id: string) =>
    api.put<Booking>(`/bookings/${id}/confirm`, {}),

  // DELETE /bookings/:id — cancel booking; optionally returns session hours
  cancel: (id: string, returnHours?: boolean) =>
    api.delete<void>(`/bookings/${id}${returnHours ? '?return_hours=true' : ''}`),
}
