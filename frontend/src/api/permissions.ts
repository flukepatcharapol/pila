// =============================================================================
// api/permissions.ts — Permission matrix and feature toggle API service
// The permission matrix controls which roles can perform which actions on which
// modules. Feature toggles enable/disable entire module sections globally.
// =============================================================================

import { api } from '@/api/client'
import type { PermissionCell, FeatureToggle, Role } from '@/types'

export const permissionsApi = {
  // GET /permissions — full permission matrix for roles below current user's role
  // Returns all PermissionCell entries (role × module × action)
  getMatrix: () =>
    api.get<PermissionCell[]>('/permissions'),

  // PUT /permissions — update one or more permission cells
  // Pass an array of changed cells; BE performs an upsert
  update: (cells: PermissionCell[]) =>
    api.put<void>('/permissions', { cells }),

  // GET /permissions/:role — permissions for a specific role only
  getByRole: (role: Role) =>
    api.get<PermissionCell[]>(`/permissions/${role}`),

  // GET /permissions/feature-toggles — module-level on/off switches
  // Fetched by AuthContext on mount so FeatureGate components work everywhere
  getFeatureToggles: () =>
    api.get<FeatureToggle[]>('/permissions/feature-toggles'),

  // PUT /permissions/feature-toggles — enable or disable a module (owner+ only)
  updateFeatureToggle: (module: string, enabled: boolean) =>
    api.put<void>('/permissions/feature-toggles', { module, enabled }),
}
