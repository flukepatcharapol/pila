// =============================================================================
// api/customers.ts — Customer management API service
// All list endpoints accept ListParams; IDs are UUIDs but dropdowns show
// display_name + code per CR-01 (never show raw UUIDs in the UI).
// =============================================================================

import { api } from '@/api/client'
import type { Customer, PaginatedResponse, ListParams } from '@/types'

// Build a URL query string from an optional params object.
// Only non-null, non-undefined, non-empty values are included.
function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const customersApi = {
  // GET /customers — paginated list with optional search/filter
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<Customer>>(`/customers${toQuery(params)}`),

  // GET /customers/:id — single customer with remaining_hours balance
  get: (id: string) =>
    api.get<Customer>(`/customers/${id}`),

  // POST /customers — create new customer; backend auto-generates customer code
  create: (body: Partial<Customer>) =>
    api.post<Customer>('/customers', body),

  // PUT /customers/:id — update customer fields
  update: (id: string, body: Partial<Customer>) =>
    api.put<Customer>(`/customers/${id}`, body),

  // DELETE /customers/:id — returns 204 No Content on success
  delete: (id: string) =>
    api.delete<void>(`/customers/${id}`),
}
