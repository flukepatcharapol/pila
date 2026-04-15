// =============================================================================
// api/caretakers.ts — Caretaker (ผู้ดูแลเด็ก) management API service
// Caretakers are assigned to child customers and are branch-scoped.
// =============================================================================

import { api } from '@/api/client'
import type { Caretaker, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const caretakersApi = {
  // GET /caretakers — paginated, filterable by branch_id and status
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<Caretaker>>(`/caretakers${toQuery(params)}`),

  // GET /caretakers/:id — single caretaker detail
  get: (id: string) =>
    api.get<Caretaker>(`/caretakers/${id}`),

  // POST /caretakers — create new caretaker
  create: (body: Partial<Caretaker>) =>
    api.post<Caretaker>('/caretakers', body),

  // PUT /caretakers/:id — update including status toggle (active/inactive)
  update: (id: string, body: Partial<Caretaker>) =>
    api.put<Caretaker>(`/caretakers/${id}`, body),

  // DELETE /caretakers/:id — hard delete; no guard needed per BE
  delete: (id: string) =>
    api.delete<void>(`/caretakers/${id}`),
}
