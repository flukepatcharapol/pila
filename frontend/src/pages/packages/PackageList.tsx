// =============================================================================
// pages/packages/PackageList.tsx — Package management list
// =============================================================================

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useTable } from '@/hooks/useTable'
import { packagesApi } from '@/api/packages'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Package } from '@/types'

export default function PackageList() {
  usePageTitle('แพ็กเกจ')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data, total, isLoading, params, setPage, setStatus, refresh } = useTable(packagesApi.list)
  const [deleteTarget, setDeleteTarget] = useState<Package | null>(null)
  const [isDeleting, setIsDeleting]     = useState(false)

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    try {
      await packagesApi.delete(deleteTarget.id)
      toast.success('ลบแพ็กเกจสำเร็จ')
      setDeleteTarget(null); refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ — อาจมีคำสั่งซื้อที่ใช้แพ็กเกจนี้อยู่')
    } finally { setIsDeleting(false) }
  }

  const columns: TableColumn<Package>[] = [
    { key: 'name',  label: 'ชื่อแพ็กเกจ', sortable: true },
    { key: 'hours', label: 'ชั่วโมง',     render: (r) => <span className="tabular-nums">{r.hours} ชม.</span> },
    { key: 'type',  label: 'ประเภท',      render: (r) => <span>{r.type === 'sale' ? 'ขายปกติ' : 'Pre-sale'}</span> },
    { key: 'price', label: 'ราคา',        render: (r) => <span className="tabular-nums">{r.price.toLocaleString()} ฿</span> },
    {
      key: 'status', label: 'สถานะ',
      render: (r) => {
        const labelMap: Record<string, string> = { active: 'ใช้งาน', inactive: 'ระงับ', expired: 'หมดอายุ' }
        return <StatusBadge label={labelMap[r.status] ?? r.status} variant={resolveStatusVariant(r.status)} />
      },
    },
    {
      key: 'active_period', label: 'ช่วงเวลา',
      render: (r) => <span className="text-body-sm text-on-surface-variant">{r.active_from ?? '∞'} – {r.active_until ?? '∞'}</span>,
    },
    {
      key: 'actions', label: '',
      render: (r) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/packages/${r.id}/edit`)}>แก้ไข</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>ลบ</Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-3">
          <div className="w-40"><Select options={[{ value: '', label: 'ทุกสถานะ' }, { value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }, { value: 'expired', label: 'หมดอายุ' }]} value={params.status ?? ''} onChange={(e) => setStatus(e.target.value || null)} /></div>
        </div>
        <Button variant="primary" onClick={() => navigate('/packages/new')} data-testid="package-list-add-btn">+ เพิ่มแพ็กเกจ</Button>
      </div>
      <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบแพ็กเกจ" rowKey={(r) => r.id} />
      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />
      <ConfirmDialog isOpen={!!deleteTarget} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)}
        title="ลบแพ็กเกจ" description={`ต้องการลบ "${deleteTarget?.name}" ใช่ไหม?`} confirmLabel="ลบ" isDanger isLoading={isDeleting} />
    </div>
  )
}
