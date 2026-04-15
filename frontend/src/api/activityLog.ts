// =============================================================================
// api/activityLog.ts — Activity log (audit trail) API service
// Every create/update/delete action is logged on the backend with before/after
// diff. This read-only endpoint exposes that trail for admin review.
// =============================================================================

import { api } from '@/api/client'
import type { ActivityLogEntry, PaginatedResponse, ListParams } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

// Additional filters specific to the activity log beyond base ListParams
interface ActivityLogParams extends ListParams {
  action?: string      // e.g. "CREATE_ORDER", "DEDUCT_SESSION"
  target_type?: string // e.g. "Customer", "Order"
  target_id?: string   // UUID of the specific record being filtered on
  actor_id?: string    // filter by who performed the action
}

export const activityLogApi = {
  // GET /activity-log — paginated audit trail with optional filters
  // Supports: date range, actor, action type, target type, branch
  list: (params?: ActivityLogParams) =>
    api.get<PaginatedResponse<ActivityLogEntry>>(`/activity-log${toQuery(params)}`),
}
