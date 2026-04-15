// =============================================================================
// pages/customers/CustomerDetail.tsx — Read-only customer profile page
// Shows full customer info + remaining hours card + order history table.
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { customersApi } from '@/api/customers'
import { ordersApi } from '@/api/orders'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Customer, Order } from '@/types'

export default function CustomerDetail() {
  usePageTitle('รายละเอียดลูกค้า')
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { user } = useAuth()

  const [customer, setCustomer]   = useState<Customer | null>(null)
  const [orders, setOrders]       = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showDelete, setShowDelete] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const canDelete = user?.role !== 'trainer'

  // Fetch customer + recent orders on mount
  useEffect(() => {
    if (!id) return
    setIsLoading(true)
    Promise.all([
      customersApi.get(id),
      ordersApi.list({ customer_id: id, page_size: 10, sort_by: 'order_date', sort_dir: 'desc' }),
    ])
      .then(([c, o]) => {
        setCustomer(c)
        setOrders(o.items)
      })
      .catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ'))
      .finally(() => setIsLoading(false))
  }, [id])

  async function handleDelete() {
    if (!id || !customer) return
    setIsDeleting(true)
    try {
      await customersApi.delete(id)
      toast.success('ลบลูกค้าสำเร็จ')
      navigate('/customers')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ')
    } finally {
      setIsDeleting(false)
    }
  }

  const orderColumns: TableColumn<Order>[] = [
    { key: 'order_date',    label: 'วันที่',       sortable: false },
    { key: 'package_name',  label: 'แพ็กเกจ',     sortable: false },
    { key: 'hours',         label: 'ชั่วโมง',     sortable: false,
      render: (r) => <span>{r.hours + r.bonus_hours} ชม.</span> },
    { key: 'price',         label: 'ราคา',        sortable: false,
      render: (r) => <span>{r.price.toLocaleString()} ฿</span> },
    { key: 'outstanding_balance', label: 'ค้างชำระ', sortable: false,
      render: (r) => (
        <span className={r.outstanding_balance > 0 ? 'text-error font-semibold' : 'text-tertiary'}>
          {r.outstanding_balance.toLocaleString()} ฿
        </span>
      ),
    },
    { key: 'status', label: 'สถานะ', sortable: false,
      render: (r) => <StatusBadge label={r.status} variant={resolveStatusVariant(r.status)} />,
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-body-md text-on-surface-variant">ไม่พบข้อมูลลูกค้า</p>
        <Button variant="ghost" onClick={() => navigate('/customers')}>กลับ</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* ── Back + actions ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/customers')}>
          ← กลับ
        </Button>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => navigate(`/customers/${id}/edit`)}
            data-testid="customer-detail-edit-btn"
          >
            แก้ไข
          </Button>
          {canDelete && (
            <Button
              variant="danger"
              onClick={() => setShowDelete(true)}
              data-testid="customer-detail-delete-btn"
            >
              ลบ
            </Button>
          )}
        </div>
      </div>

      {/* ── Profile card ── */}
      <div className="bg-surface-container-lowest rounded-xl p-6 shadow-ambient space-y-4">
        <div className="flex items-start gap-4">
          {/* Avatar */}
          <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center shrink-0">
            <span className="text-on-secondary text-headline-sm font-bold">
              {customer.display_name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-headline-sm font-display font-bold text-on-surface">
              {customer.display_name}
            </h2>
            {customer.nickname && (
              <p className="text-body-md text-on-surface-variant">({customer.nickname})</p>
            )}
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="font-mono text-label-md text-secondary bg-secondary/10 px-2 py-0.5 rounded">
                {customer.code}
              </span>
              <StatusBadge
                label={customer.status === 'active' ? 'ใช้งาน' : 'ระงับ'}
                variant={resolveStatusVariant(customer.status)}
              />
              {customer.is_duplicate && (
                <StatusBadge label="ซ้ำ" variant="pending" />
              )}
            </div>
          </div>

          {/* Remaining hours — prominent card */}
          <div className="shrink-0 text-center px-4 py-3 rounded-xl border-2 border-tertiary/30 bg-tertiary/5">
            <p className="text-display-sm font-display font-bold text-tertiary tabular-nums">
              {customer.remaining_hours}
            </p>
            <p className="text-label-sm text-on-surface-variant">เซสชันคงเหลือ</p>
          </div>
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 pt-4 border-t border-outline-variant">
          {[
            { label: 'ชื่อ-นามสกุล', value: `${customer.first_name} ${customer.last_name}` },
            { label: 'เบอร์โทร',     value: customer.phone ?? '—' },
            { label: 'LINE ID',       value: customer.line_id ?? '—' },
            { label: 'อีเมล',         value: customer.email ?? '—' },
            { label: 'วันเกิด',       value: customer.birthday ?? '—' },
            { label: 'หมายเหตุ',      value: customer.notes ?? '—' },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-label-sm text-on-surface-variant">{label}</p>
              <p className="text-body-md text-on-surface leading-thai">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Order history ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-title-md font-display font-semibold text-on-surface">
            ประวัติคำสั่งซื้อ
          </h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/orders/new')}
            data-testid="customer-detail-add-order-btn"
          >
            + คำสั่งซื้อใหม่
          </Button>
        </div>
        <Table
          columns={orderColumns}
          data={orders}
          isLoading={false}
          emptyMessage="ยังไม่มีคำสั่งซื้อ"
          rowKey={(r) => r.id}
        />
      </div>

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={showDelete}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
        title="ลบลูกค้า"
        description={`ต้องการลบ "${customer.display_name}" ออกจากระบบใช่ไหม? การกระทำนี้ไม่สามารถยกเลิกได้`}
        confirmLabel="ลบ"
        isDanger
        isLoading={isDeleting}
      />
    </div>
  )
}
