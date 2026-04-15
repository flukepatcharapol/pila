// =============================================================================
// api/dashboard.ts — Dashboard metrics API service
// The backend returns role-appropriate metrics: trainers see their own stats,
// owners see multi-branch aggregates, etc.
// =============================================================================

import { api } from '@/api/client'
import type { DashboardData } from '@/types'

// Time period granularity supported by GET /dashboard
export type DashboardPeriod = 'today' | 'week' | 'month' | 'custom'

// Custom date range parameters (only required when period = 'custom')
export interface DashboardParams {
  period: DashboardPeriod
  branch_id?: string   // optional: filter by branch (owner/developer only)
  start_date?: string  // ISO date "YYYY-MM-DD", required if period = 'custom'
  end_date?: string    // ISO date "YYYY-MM-DD", required if period = 'custom'
}

export const dashboardApi = {
  // GET /dashboard — aggregate KPI metrics filtered by period and optional branch
  // Response shape varies by role (trainer sees own hours, owner sees revenue, etc.)
  get: (params: DashboardParams) => {
    // Build query string — only include non-null values
    const q = new URLSearchParams()
    q.set('period', params.period)
    if (params.branch_id) q.set('branch_id', params.branch_id)
    if (params.start_date) q.set('start_date', params.start_date)
    if (params.end_date) q.set('end_date', params.end_date)
    return api.get<DashboardData>(`/dashboard?${q.toString()}`)
  },
}
