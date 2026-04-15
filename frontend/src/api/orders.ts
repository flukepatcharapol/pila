// =============================================================================
// api/orders.ts — Order management API service
// Orders represent package purchases. Each order tracks payment installments
// and calculates an outstanding_balance = price - sum(payments).
// =============================================================================

import { api } from '@/api/client'
import type { Order, OrderPayment, PaginatedResponse, ListParams, PaymentMethod } from '@/types'

function toQuery(params?: ListParams): string {
  if (!params) return ''
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v))
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const ordersApi = {
  // GET /orders — paginated, filterable by date range / branch / customer
  list: (params?: ListParams) =>
    api.get<PaginatedResponse<Order>>(`/orders${toQuery(params)}`),

  // GET /orders/:id — full order detail including payments[]
  get: (id: string) =>
    api.get<Order>(`/orders/${id}`),

  // POST /orders — create new order; triggers invoice/receipt email if configured
  create: (body: Partial<Order>) =>
    api.post<Order>('/orders', body),

  // PUT /orders/:id — update mutable fields (payment method, notes, paid amount)
  update: (id: string, body: Partial<Order>) =>
    api.put<Order>(`/orders/${id}`, body),

  // DELETE /orders/:id — soft delete; returns 204 No Content
  delete: (id: string) =>
    api.delete<void>(`/orders/${id}`),

  // POST /orders/:id/payments — record an installment payment
  // Updates order.outstanding_balance = price - total_paid automatically on BE
  addPayment: (id: string, body: { method: PaymentMethod; amount: number; paid_at?: string }) =>
    api.post<OrderPayment>(`/orders/${id}/payments`, body),

  // GET /orders/:id/payments — list all installment payments for an order
  getPayments: (id: string) =>
    api.get<OrderPayment[]>(`/orders/${id}/payments`),

  // POST /orders/:id/receipt — resend receipt/invoice email to customer
  resendReceipt: (id: string) =>
    api.post<void>(`/orders/${id}/receipt`, {}),
}
