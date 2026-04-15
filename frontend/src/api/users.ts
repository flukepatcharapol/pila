// =============================================================================
// api/users.ts — User management API service
// Users are staff accounts. Role hierarchy is enforced: you cannot create or
// promote a user to a role equal to or higher than your own.
// =============================================================================

import { api } from '@/api/client'
import type { User, Role, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

// Request body for creating a user (password is set separately via /internal/assign-password)
interface CreateUserBody {
  username: string
  display_name: string
  email: string
  role: Role
  branch_id: string | null
}

export const usersApi = {
  // GET /users — paginated list, filterable by role/branch/status
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<User>>(`/users${toQuery(params)}`),

  // GET /users/:id — single user profile
  get: (id: string) =>
    api.get<User>(`/users/${id}`),

  // POST /users — create user; password assigned separately by admin workflow
  create: (body: CreateUserBody) =>
    api.post<User>('/users', body),

  // PUT /users/:id — update mutable fields (display_name, email, branch_id)
  update: (id: string, body: Partial<User>) =>
    api.put<User>(`/users/${id}`, body),

  // PUT /users/:id/role — change role (role-gated: cannot promote above own role)
  setRole: (id: string, role: Role) =>
    api.put<User>(`/users/${id}/role`, { role }),

  // DELETE /users/:id — deactivates the account (guard: not own account, not higher role)
  delete: (id: string) =>
    api.delete<void>(`/users/${id}`),
}
