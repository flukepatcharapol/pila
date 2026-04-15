// =============================================================================
// api/branches.ts — Branch management API service
// Branches are studio locations. Each branch has source types (referral codes)
// and opening/closing hours used for booking validation.
// =============================================================================

import { api } from '@/api/client'
import type { Branch, BranchDetail, SourceType, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const branchesApi = {
  // GET /branches — list all branches visible to the current user
  // owner/developer sees all; branch_master/admin/trainer sees only their branch
  list: (params?: ListParams) =>
    api.get<Branch[]>(`/branches${toQuery(params)}`),

  // GET /branches/:id — full branch detail including source_types and hours
  get: (id: string) =>
    api.get<BranchDetail>(`/branches/${id}`),

  // POST /branches — create branch (owner+ only)
  create: (body: Partial<Branch>) =>
    api.post<Branch>('/branches', body),

  // PUT /branches/:id — update branch config including opening/closing hours
  update: (id: string, body: Partial<BranchDetail>) =>
    api.put<BranchDetail>(`/branches/${id}`, body),

  // DELETE /branches/:id — 409 if branch has any customers
  delete: (id: string) =>
    api.delete<void>(`/branches/${id}`),

  // GET /branches/:id/source-types — referral/enrollment source codes for branch
  // Used in CustomerForm to populate the source type chip selector (CR-02)
  getSourceTypes: (branchId: string) =>
    api.get<SourceType[]>(`/branches/${branchId}/source-types`),

  // POST /branches/:id/source-types — add a new source type to this branch
  createSourceType: (branchId: string, body: Partial<SourceType>) =>
    api.post<SourceType>(`/branches/${branchId}/source-types`, body),

  // PUT /branches/:id/source-types/:typeId — update a source type label/code
  updateSourceType: (branchId: string, typeId: string, body: Partial<SourceType>) =>
    api.put<SourceType>(`/branches/${branchId}/source-types/${typeId}`, body),
}
