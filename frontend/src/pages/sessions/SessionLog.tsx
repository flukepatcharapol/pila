// =============================================================================
// pages/sessions/SessionLog.tsx — Full session transaction log with filters
// =============================================================================

import { usePageTitle } from '@/hooks/usePageTitle'
import { useTable } from '@/hooks/useTable'
import { sessionsApi } from '@/api/sessions'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Input } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import type { SessionLogEntry } from '@/types'

export default function SessionLog() {
  usePageTitle('Session Log')

  const { data, total, isLoading, params, setSearch, setPage, setExtraParams } = useTable(sessionsApi.log)

  const columns: TableColumn<SessionLogEntry>[] = [
    {
      key: 'created_at', label: 'วันเวลา',
      render: (r) => <span className="text-body-sm text-on-surface-variant">{r.created_at.slice(0, 16).replace('T', ' ')}</span>,
    },
    {
      key: 'customer_code', label: 'รหัสลูกค้า',
      render: (r) => <span className="font-mono text-label-md text-secondary">{r.customer_code}</span>,
    },
    { key: 'customer_name', label: 'ชื่อลูกค้า' },
    {
      key: 'transaction_type', label: 'ประเภท',
      render: (r) => (
        <span className={`text-label-md font-semibold ${r.transaction_type === 'DEDUCT' ? 'text-error' : r.transaction_type === 'ADD' ? 'text-tertiary' : 'text-secondary'}`}>
          {r.transaction_type}
        </span>
      ),
    },
    { key: 'before', label: 'ก่อน',   render: (r) => <span className="tabular-nums">{r.before}</span> },
    {
      key: 'amount', label: 'จำนวน',
      render: (r) => (
        <span className={`tabular-nums font-semibold ${r.amount < 0 ? 'text-error' : 'text-tertiary'}`}>
          {r.amount > 0 ? `+${r.amount}` : r.amount}
        </span>
      ),
    },
    { key: 'after',  label: 'หลัง',   render: (r) => <span className="tabular-nums font-semibold">{r.after}</span> },
    { key: 'actor_name',   label: 'ผู้ทำรายการ' },
    { key: 'trainer_name', label: 'เทรนเนอร์', render: (r) => <span>{r.trainer_name ?? '—'}</span> },
  ]

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="w-full md:w-64">
          <Input placeholder="ค้นหาชื่อลูกค้า…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="session-log-search" />
        </div>
        <DatePicker label="ตั้งแต่" value={params.start_date ?? null} onChange={(v) => setExtraParams({ start_date: v ?? undefined, page: 1 })} />
        <DatePicker label="ถึง"     value={params.end_date   ?? null} onChange={(v) => setExtraParams({ end_date:   v ?? undefined, page: 1 })} />
      </div>

      <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบรายการ" rowKey={(r) => r.id} />
      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />
    </div>
  )
}
