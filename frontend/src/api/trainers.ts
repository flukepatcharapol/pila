// =============================================================================
// api/trainers.ts — Trainer management API service
// Trainers are branch-scoped staff members who conduct training sessions.
// Delete is guarded on the BE: 409 Conflict if trainer has active customers/bookings.
// =============================================================================

import { api } from '@/api/client'
import type { Trainer, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const trainersApi = {
  // GET /trainers — list trainers, filterable by branch_id and status
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<Trainer>>(`/trainers${toQuery(params)}`),

  // GET /trainers/:id — single trainer detail
  get: (id: string) =>
    api.get<Trainer>(`/trainers/${id}`),

  // POST /trainers — create trainer; display_name auto-derived from name on BE
  create: (body: Partial<Trainer>) =>
    api.post<Trainer>('/trainers', body),

  // PUT /trainers/:id — update trainer fields including status toggle
  update: (id: string, body: Partial<Trainer>) =>
    api.put<Trainer>(`/trainers/${id}`, body),

  // DELETE /trainers/:id — returns 409 if trainer has active bookings or customers
  delete: (id: string) =>
    api.delete<void>(`/trainers/${id}`),
}
