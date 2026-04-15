// =============================================================================
// api/packages.ts — Package management API service
// Packages define training hour bundles (e.g. "10h Sale Package 3,500 THB").
// Delete is guarded: 409 Conflict if the package is referenced in any order.
// =============================================================================

import { api } from '@/api/client'
import type { Package, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

// Extra filter not in ListParams base — only return packages available for purchase
interface PackageListParams extends ListParams {
  active_only?: boolean
}

export const packagesApi = {
  // GET /packages — filterable by branch, type, status, and active_only flag
  list: (params?: PackageListParams) =>
    api.get<PaginatedResponse<Package>>(`/packages${toQuery(params)}`),

  // GET /packages/:id — single package detail
  get: (id: string) =>
    api.get<Package>(`/packages/${id}`),

  // POST /packages — create; branch_id null = available across all branches
  create: (body: Partial<Package>) =>
    api.post<Package>('/packages', body),

  // PUT /packages/:id — update including status toggle and date range
  update: (id: string, body: Partial<Package>) =>
    api.put<Package>(`/packages/${id}`, body),

  // DELETE /packages/:id — 409 if package is in use by any order
  delete: (id: string) =>
    api.delete<void>(`/packages/${id}`),
}
