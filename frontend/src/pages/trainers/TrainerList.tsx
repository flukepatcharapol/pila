// =============================================================================
// pages/trainers/TrainerList.tsx — Trainer directory with card/table toggle
// =============================================================================

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useTable } from '@/hooks/useTable'
import { trainersApi } from '@/api/trainers'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Trainer } from '@/types'

export default function TrainerList() {
  usePageTitle('เทรนเนอร์')
  const navigate = useNavigate()
  const { toast } = useToast()

  const { data, total, isLoading, params, setSearch, setPage, setStatus, refresh } = useTable(trainersApi.list)

  const [deleteTarget, setDeleteTarget] = useState<Trainer | null>(null)
  const [isDeleting, setIsDeleting]     = useState(false)
  // Toggle between card grid and table view; persist choice
  const [view, setView] = useState<'card' | 'table'>(
    (localStorage.getItem('trainer_view') as 'card' | 'table') ?? 'card',
  )

  function switchView(v: 'card' | 'table') {
    setView(v)
    localStorage.setItem('trainer_view', v)
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    try {
      await trainersApi.delete(deleteTarget.id)
      toast.success(`ลบเทรนเนอร์ "${deleteTarget.display_name}" สำเร็จ`)
      setDeleteTarget(null)
      refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ — อาจมีลูกค้าหรือการจองที่ยังใช้งานอยู่')
    } finally {
      setIsDeleting(false)
    }
  }

  const columns: TableColumn<Trainer>[] = [
    { key: 'display_name', label: 'ชื่อ', sortable: true },
    { key: 'email',        label: 'อีเมล', render: (r) => <span>{r.email ?? '—'}</span> },
    { key: 'status',       label: 'สถานะ', render: (r) => <StatusBadge label={r.status === 'active' ? 'ใช้งาน' : 'ระงับ'} variant={resolveStatusVariant(r.status)} /> },
    {
      key: 'actions', label: '',
      render: (r) => (
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" size="sm" onClick={() => navigate(`/trainers/${r.id}/edit`)}>แก้ไข</Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget(r)}>ลบ</Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <div className="w-64"><Input placeholder="ค้นหาชื่อ…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="trainer-list-search" /></div>
          <div className="w-36"><Select options={[{ value: '', label: 'ทุกสถานะ' }, { value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }]} value={params.status ?? ''} onChange={(e) => setStatus(e.target.value || null)} /></div>
        </div>
        <div className="flex gap-2">
          {/* View toggle */}
          <div className="flex rounded-lg border border-outline-variant overflow-hidden">
            {(['card', 'table'] as const).map((v) => (
              <button key={v} type="button" onClick={() => switchView(v)}
                className={`px-3 py-1.5 text-label-md transition-colors ${view === v ? 'bg-secondary text-on-secondary' : 'text-on-surface-variant hover:bg-surface-container-low'}`}>
                {v === 'card' ? '⊞' : '☰'}
              </button>
            ))}
          </div>
          <Button variant="primary" onClick={() => navigate('/trainers/new')} data-testid="trainer-list-add-btn">+ เพิ่มเทรนเนอร์</Button>
        </div>
      </div>

      {view === 'table' ? (
        <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบเทรนเนอร์" rowKey={(r) => r.id} />
      ) : (
        isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-36 rounded-xl bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer" />)}
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-32 rounded-xl border border-outline-variant bg-surface-container-low">
            <p className="text-body-md text-on-surface-variant">ไม่พบเทรนเนอร์</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.map((trainer) => (
              <div key={trainer.id} className="bg-surface-container-lowest rounded-xl p-4 shadow-ambient flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center shrink-0">
                    <span className="text-on-secondary font-semibold">{trainer.display_name.charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body-md font-semibold text-on-surface truncate">{trainer.display_name}</p>
                    <p className="text-body-sm text-on-surface-variant truncate">{trainer.email ?? '—'}</p>
                  </div>
                </div>
                <StatusBadge label={trainer.status === 'active' ? 'ใช้งาน' : 'ระงับ'} variant={resolveStatusVariant(trainer.status)} />
                <div className="flex gap-2 mt-auto">
                  <Button variant="ghost" size="sm" className="flex-1" onClick={() => navigate(`/trainers/${trainer.id}/edit`)}>แก้ไข</Button>
                  <Button variant="danger" size="sm" onClick={() => setDeleteTarget(trainer)}>ลบ</Button>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />
      <ConfirmDialog isOpen={!!deleteTarget} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)}
        title="ลบเทรนเนอร์" description={`ต้องการลบ "${deleteTarget?.display_name}" ใช่ไหม?`} confirmLabel="ลบ" isDanger isLoading={isDeleting} />
    </div>
  )
}
