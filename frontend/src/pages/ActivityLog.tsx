// =============================================================================
// pages/ActivityLog.tsx — Audit trail with before/after diff viewer
// =============================================================================

import { useState } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useTable } from '@/hooks/useTable'
import { activityLogApi } from '@/api/activityLog'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Input } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Modal } from '@/components/ui/Modal'
import type { ActivityLogEntry } from '@/types'

export default function ActivityLog() {
  usePageTitle('Activity Log')

  const { data, total, isLoading, params, setSearch, setPage, setExtraParams } = useTable(activityLogApi.list)
  const [diffEntry, setDiffEntry] = useState<ActivityLogEntry | null>(null)

  const columns: TableColumn<ActivityLogEntry>[] = [
    { key: 'created_at', label: 'เวลา',    render: (r) => <span className="text-body-sm text-on-surface-variant">{r.created_at.slice(0, 16).replace('T', ' ')}</span> },
    { key: 'actor_name', label: 'ผู้ทำ' },
    { key: 'action',     label: 'Action', render: (r) => <span className="font-mono text-label-md text-secondary">{r.action}</span> },
    { key: 'target_type', label: 'เป้าหมาย' },
    {
      key: 'changes', label: 'การเปลี่ยนแปลง',
      render: (r) =>
        r.changes ? (
          <button type="button" className="text-secondary text-label-md hover:underline" onClick={() => setDiffEntry(r)} data-testid={`activity-diff-${r.id}`}>
            ดูรายละเอียด
          </button>
        ) : <span className="text-on-surface-variant">—</span>,
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <div className="w-64"><Input placeholder="ค้นหาผู้ทำรายการ, action…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="activity-log-search" /></div>
        <DatePicker label="ตั้งแต่" value={params.start_date ?? null} onChange={(v) => setExtraParams({ start_date: v ?? undefined, page: 1 })} />
        <DatePicker label="ถึง"     value={params.end_date   ?? null} onChange={(v) => setExtraParams({ end_date:   v ?? undefined, page: 1 })} />
      </div>

      <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบรายการ" rowKey={(r) => r.id} />
      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />

      {/* Diff viewer modal */}
      <Modal isOpen={!!diffEntry} onClose={() => setDiffEntry(null)} title={`เปลี่ยนแปลง: ${diffEntry?.action}`} size="md">
        {diffEntry?.changes && (
          <div className="space-y-3">
            {Object.entries(diffEntry.changes).map(([field, { before, after }]) => (
              <div key={field} className="rounded-lg border border-outline-variant overflow-hidden">
                <div className="px-3 py-1.5 bg-surface-container-low border-b border-outline-variant">
                  <span className="text-label-md font-semibold text-on-surface">{field}</span>
                </div>
                <div className="grid grid-cols-2 divide-x divide-outline-variant">
                  <div className="px-3 py-2 bg-error-container/10">
                    <p className="text-label-sm text-error mb-1">ก่อน</p>
                    <p className="text-body-sm text-on-surface font-mono break-all">{JSON.stringify(before) ?? '—'}</p>
                  </div>
                  <div className="px-3 py-2 bg-tertiary/5">
                    <p className="text-label-sm text-tertiary mb-1">หลัง</p>
                    <p className="text-body-sm text-on-surface font-mono break-all">{JSON.stringify(after) ?? '—'}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
