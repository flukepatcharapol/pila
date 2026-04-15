// =============================================================================
// pages/caretakers/CaretakerList.tsx — Caretaker (ผู้ดูแลเด็ก) list
// =============================================================================

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useTable } from '@/hooks/useTable'
import { caretakersApi } from '@/api/caretakers'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Caretaker } from '@/types'

export default function CaretakerList() {
  usePageTitle('ผู้ดูแลเด็ก')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data, total, isLoading, params, setSearch, setPage, refresh } = useTable(caretakersApi.list)
  const [deleteTarget, setDeleteTarget] = useState<Caretaker | null>(null)
  const [isDeleting, setIsDeleting]     = useState(false)

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    try {
      await caretakersApi.delete(deleteTarget.id)
      toast.success('ลบผู้ดูแลเด็กสำเร็จ')
      setDeleteTarget(null); refresh()
    } catch (err) { toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ') }
    finally { setIsDeleting(false) }
  }

  const columns: TableColumn<Caretaker>[] = [
    { key: 'name',   label: 'ชื่อ', sortable: true },
    { key: 'email',  label: 'อีเมล', render: (r) => <span>{r.email ?? '—'}</span> },
    { key: 'status', label: 'สถานะ', render: (r) => <StatusBadge label={r.status === 'active' ? 'ใช้งาน' : 'ระงับ'} variant={resolveStatusVariant(r.status)} /> },
    {
      key: 'actions', label: '',
      render: (r) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/caretakers/${r.id}/edit`)}>แก้ไข</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>ลบ</Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="w-64"><Input placeholder="ค้นหาชื่อ…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="caretaker-list-search" /></div>
        <Button variant="primary" onClick={() => navigate('/caretakers/new')} data-testid="caretaker-list-add-btn">+ เพิ่มผู้ดูแล</Button>
      </div>
      <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบผู้ดูแลเด็ก" rowKey={(r) => r.id} />
      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />
      <ConfirmDialog isOpen={!!deleteTarget} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)}
        title="ลบผู้ดูแลเด็ก" description={`ต้องการลบ "${deleteTarget?.name}" ใช่ไหม?`} confirmLabel="ลบ" isDanger isLoading={isDeleting} />
    </div>
  )
}
