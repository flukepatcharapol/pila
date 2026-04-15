// =============================================================================
// api/sessions.ts — Session (customer training hours) API service
// Note: the backend routes are under /customer-hours, not /sessions.
// This service provides a friendlier name for the FE layer.
// =============================================================================

import { api } from '@/api/client'
import type {
  SessionLogEntry,
  DeductSessionPayload,
  AdjustHoursPayload,
  PaginatedResponse,
  ListParams,
} from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

// Response shape from POST /customer-hours/deduct
interface DeductResult {
  customer_id: string
  remaining_hours: number  // updated balance after deduction
}

// Response shape from GET /customer-hours/remaining/:id
interface RemainingHours {
  customer_id: string
  remaining_hours: number
}

// Response shape from GET /customer-hours/trainer-report
interface TrainerReportEntry {
  trainer_id: string
  trainer_name: string
  total_hours: number
  session_count: number
}

export const sessionsApi = {
  // POST /customer-hours/deduct — subtract exactly 1 hour from a customer
  // Uses SELECT FOR UPDATE on the DB row to prevent race conditions (double-deduct)
  deduct: (body: DeductSessionPayload) =>
    api.post<DeductResult>('/customer-hours/deduct', body),

  // PUT /customer-hours/adjust — manual correction, supports + or - amounts
  // Requires a reason string for audit trail visibility
  adjust: (body: AdjustHoursPayload) =>
    api.put<DeductResult>('/customer-hours/adjust', body),

  // GET /customer-hours/remaining/:id — current hour balance for one customer
  getRemaining: (customerId: string) =>
    api.get<RemainingHours>(`/customer-hours/remaining/${customerId}`),

  // GET /customer-hours/log — paginated transaction ledger
  // Supports date range, branch, customer, and trainer filters
  log: (params?: ListParams) =>
    api.get<PaginatedResponse<SessionLogEntry>>(`/customer-hours/log${toQuery(params)}`),

  // GET /customer-hours/trainer-report — hours trained per trainer in a date range
  trainerReport: (params?: ListParams) =>
    api.get<TrainerReportEntry[]>(`/customer-hours/trainer-report${toQuery(params)}`),
}
