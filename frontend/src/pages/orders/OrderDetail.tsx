// =============================================================================
// pages/orders/OrderDetail.tsx — Order detail with payment history
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { ordersApi } from '@/api/orders'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ApiError } from '@/api/client'
import type { Order, OrderPayment, PaymentMethod } from '@/types'

export default function OrderDetail() {
  usePageTitle('รายละเอียดคำสั่งซื้อ')
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [order, setOrder]         = useState<Order | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showPayment, setShowPayment] = useState(false)
  const [payMethod, setPayMethod] = useState<PaymentMethod>('cash')
  const [payAmount, setPayAmount] = useState('')
  const [isSaving, setIsSaving]   = useState(false)

  useEffect(() => {
    if (!id) return
    ordersApi.get(id)
      .then(setOrder)
      .catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ'))
      .finally(() => setIsLoading(false))
  }, [id])

  async function handleAddPayment() {
    if (!id || !payAmount) return
    setIsSaving(true)
    try {
      await ordersApi.addPayment(id, { method: payMethod, amount: Number(payAmount) })
      toast.success('บันทึกการชำระเงินสำเร็จ')
      setShowPayment(false)
      setPayAmount('')
      // Re-fetch to update outstanding_balance
      ordersApi.get(id).then(setOrder).catch(() => {})
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleResendReceipt() {
    if (!id) return
    try {
      await ordersApi.resendReceipt(id)
      toast.success('ส่งใบเสร็จสำเร็จ')
    } catch {
      toast.error('ส่งใบเสร็จไม่สำเร็จ')
    }
  }

  const paymentColumns: TableColumn<OrderPayment>[] = [
    { key: 'paid_at', label: 'วันที่',   render: (r) => <span className="text-body-sm">{r.paid_at.slice(0, 10)}</span> },
    { key: 'method',  label: 'วิธีชำระ', render: (r) => <span>{r.method}</span> },
    { key: 'amount',  label: 'จำนวน',   render: (r) => <span className="tabular-nums font-semibold">{r.amount.toLocaleString()} ฿</span> },
  ]

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>
  if (!order) return <div className="p-8 text-center text-on-surface-variant">ไม่พบข้อมูล</div>

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/orders')}>← กลับ</Button>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={handleResendReceipt} data-testid="order-detail-resend-btn">ส่งใบเสร็จ</Button>
          <Button variant="secondary" onClick={() => navigate(`/orders/${id}/edit`)} data-testid="order-detail-edit-btn">แก้ไข</Button>
        </div>
      </div>

      {/* Order summary card */}
      <div className="bg-surface-container-lowest rounded-xl p-6 shadow-ambient space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-label-sm text-on-surface-variant">ลูกค้า</p>
            <p className="text-title-md font-semibold text-on-surface">{order.customer_name}</p>
            <span className="font-mono text-label-md text-secondary">{order.customer_code}</span>
          </div>
          <StatusBadge label={order.status} variant={resolveStatusVariant(order.status)} />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-outline-variant">
          {[
            { label: 'วันที่',        value: order.order_date },
            { label: 'แพ็กเกจ',      value: order.package_name },
            { label: 'ชั่วโมง',      value: `${order.hours + order.bonus_hours} ชม. (โบนัส ${order.bonus_hours})` },
            { label: 'ราคารวม',      value: `${order.price.toLocaleString()} ฿` },
            { label: 'ราคา/เซสชัน', value: `${order.price_per_session.toFixed(0)} ฿` },
            { label: 'ค้างชำระ',     value: `${order.outstanding_balance.toLocaleString()} ฿` },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-label-sm text-on-surface-variant">{label}</p>
              <p className={`text-body-md font-medium ${label === 'ค้างชำระ' && order.outstanding_balance > 0 ? 'text-error' : 'text-on-surface'}`}>{value}</p>
            </div>
          ))}
        </div>

        {order.notes && (
          <div className="pt-4 border-t border-outline-variant">
            <p className="text-label-sm text-on-surface-variant">หมายเหตุ</p>
            <p className="text-body-md text-on-surface leading-thai">{order.notes}</p>
          </div>
        )}
      </div>

      {/* Payment history */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-title-md font-display font-semibold text-on-surface">ประวัติการชำระ</h3>
          {order.outstanding_balance > 0 && (
            <Button variant="primary" size="sm" onClick={() => setShowPayment(true)} data-testid="order-detail-add-payment-btn">
              + บันทึกชำระ
            </Button>
          )}
        </div>
        <Table columns={paymentColumns} data={order.payments} isLoading={false} emptyMessage="ยังไม่มีการชำระเงิน" rowKey={(r) => r.id} />
      </div>

      {/* Add payment modal */}
      <Modal isOpen={showPayment} onClose={() => setShowPayment(false)} title="บันทึกการชำระเงิน" size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowPayment(false)}>ยกเลิก</Button>
            <Button variant="primary" onClick={handleAddPayment} isLoading={isSaving} data-testid="payment-modal-save-btn">บันทึก</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Select label="วิธีชำระเงิน"
            options={[{ value: 'cash', label: 'เงินสด' }, { value: 'bank_transfer', label: 'โอนเงิน' }, { value: 'credit', label: 'บัตรเครดิต' }]}
            value={payMethod} onChange={(e) => setPayMethod(e.target.value as PaymentMethod)} />
          <Input label="จำนวนเงิน (฿)" type="number" min="1" value={payAmount} onChange={(e) => setPayAmount(e.target.value)}
            hint={`ค้างชำระ: ${order.outstanding_balance.toLocaleString()} ฿`} data-testid="payment-amount-input" />
        </div>
      </Modal>
    </div>
  )
}
