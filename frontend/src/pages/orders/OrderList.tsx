// =============================================================================
// pages/orders/OrderList.tsx — Paginated order list with filters
// =============================================================================

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useTable } from '@/hooks/useTable'
import { useAuth } from '@/stores/AuthContext'
import { ordersApi } from '@/api/orders'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Order } from '@/types'

export default function OrderList() {
  usePageTitle('คำสั่งซื้อ')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { user } = useAuth()

  const {
    data: orders, total, isLoading, params,
    setSearch, setPage, setSort, setExtraParams, refresh,
  } = useTable(ordersApi.list)

  const [deleteTarget, setDeleteTarget] = useState<Order | null>(null)
  const [isDeleting, setIsDeleting]     = useState(false)

  const canCreate = user?.role !== 'trainer'

  const columns: TableColumn<Order>[] = [
    {
      key: 'order_date',
      label: 'วันที่',
      sortable: true,
      render: (r) => <span className="text-body-sm text-on-surface-variant">{r.order_date}</span>,
    },
    {
      key: 'customer_code',
      label: 'รหัสลูกค้า',
      render: (r) => (
        <span className="font-mono text-label-md text-secondary">{r.customer_code}</span>
      ),
    },
    {
      key: 'customer_name',
      label: 'ชื่อลูกค้า',
      sortable: true,
    },
    {
      key: 'package_name',
      label: 'แพ็กเกจ',
      render: (r) => (
        <div>
          <p className="text-body-md text-on-surface">{r.package_name}</p>
          <p className="text-body-sm text-on-surface-variant">{r.hours + r.bonus_hours} ชม.</p>
        </div>
      ),
    },
    {
      key: 'price',
      label: 'ราคา',
      sortable: true,
      render: (r) => <span className="tabular-nums">{r.price.toLocaleString()} ฿</span>,
    },
    {
      key: 'outstanding_balance',
      label: 'ค้างชำระ',
      render: (r) =>
        r.outstanding_balance > 0 ? (
          <StatusBadge label={`${r.outstanding_balance.toLocaleString()} ฿`} variant="pending" />
        ) : (
          <StatusBadge label="ชำระแล้ว" variant="active" />
        ),
    },
    {
      key: 'status',
      label: 'สถานะ',
      render: (r) => <StatusBadge label={r.status} variant={resolveStatusVariant(r.status)} />,
    },
    {
      key: 'actions',
      label: '',
      render: (r) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/orders/${r.id}`)}>ดู</Button>
          <Button variant="ghost" size="sm" onClick={() => navigate(`/orders/${r.id}/edit`)}>แก้ไข</Button>
          {canCreate && (
            <Button variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>ลบ</Button>
          )}
        </div>
      ),
    },
  ]

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    try {
      await ordersApi.delete(deleteTarget.id)
      toast.success('ลบคำสั่งซื้อสำเร็จ')
      setDeleteTarget(null)
      refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between flex-wrap">
        <div className="flex flex-wrap gap-3">
          <div className="w-full md:w-64">
            <Input placeholder="ค้นหาชื่อลูกค้า, รหัส…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="order-list-search" />
          </div>
          <DatePicker label="ตั้งแต่" value={params.start_date ?? null} onChange={(v) => setExtraParams({ start_date: v ?? undefined, page: 1 })} />
          <DatePicker label="ถึง"     value={params.end_date   ?? null} onChange={(v) => setExtraParams({ end_date:   v ?? undefined, page: 1 })} />
        </div>
        {canCreate && (
          <Button variant="primary" onClick={() => navigate('/orders/new')} data-testid="order-list-add-btn">
            + คำสั่งซื้อใหม่
          </Button>
        )}
      </div>

      <Table columns={columns} data={orders} isLoading={isLoading} emptyMessage="ไม่พบคำสั่งซื้อ"
        sortBy={params.sort_by} sortDir={params.sort_dir}
        onSort={(k) => setSort(k, params.sort_by === k && params.sort_dir === 'asc' ? 'desc' : 'asc')}
        rowKey={(r) => r.id} />

      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />

      <ConfirmDialog isOpen={!!deleteTarget} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)}
        title="ลบคำสั่งซื้อ" description="ต้องการลบคำสั่งซื้อนี้ใช่ไหม?"
        confirmLabel="ลบ" isDanger isLoading={isDeleting} />
    </div>
  )
}
