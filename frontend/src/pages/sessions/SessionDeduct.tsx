// =============================================================================
// pages/sessions/SessionDeduct.tsx — Deduct 1 session hour from a customer
// Shows branch chip → customer search → remaining hours card → deduct button
// + inline recent deduction history for the selected customer.
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { sessionsApi } from '@/api/sessions'
import { customersApi } from '@/api/customers'
import { branchesApi } from '@/api/branches'
import { BranchChip } from '@/components/ui/BranchChip'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Table, type TableColumn } from '@/components/ui/Table'
import { ApiError } from '@/api/client'
import type { Branch, Customer, SessionLogEntry } from '@/types'

export default function SessionDeduct() {
  usePageTitle('เบิกเซสชัน')
  const { toast } = useToast()
  const { activeBranchId, user } = useAuth()

  const [branches, setBranches]             = useState<Branch[]>([])
  const [selectedBranch, setSelectedBranch] = useState<string | null>(activeBranchId)
  const [customerSearch, setCustomerSearch] = useState('')
  const [customerResults, setCustomerResults] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [history, setHistory]               = useState<SessionLogEntry[]>([])
  const [isDeducting, setIsDeducting]       = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  // Load branches for chip selector
  useEffect(() => {
    branchesApi.list().then(setBranches).catch(() => {})
  }, [])

  // Sync selectedBranch when activeBranchId becomes available
  useEffect(() => {
    if (activeBranchId && !selectedBranch) setSelectedBranch(activeBranchId)
  }, [activeBranchId])

  // Debounced customer search filtered by branch
  useEffect(() => {
    if (customerSearch.length < 2) { setCustomerResults([]); return }
    const t = setTimeout(() => {
      customersApi.list({ search: customerSearch, branch_id: selectedBranch ?? undefined, page_size: 8 })
        .then((r) => setCustomerResults(r.items)).catch(() => {})
    }, 300)
    return () => clearTimeout(t)
  }, [customerSearch, selectedBranch])

  // Load recent history when a customer is selected
  useEffect(() => {
    if (!selectedCustomer) { setHistory([]); return }
    setIsLoadingHistory(true)
    sessionsApi.log({ customer_id: selectedCustomer.id, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' })
      .then((r) => setHistory(r.items))
      .catch(() => {})
      .finally(() => setIsLoadingHistory(false))
  }, [selectedCustomer])

  async function handleDeduct() {
    if (!selectedCustomer || !selectedBranch) return
    setIsDeducting(true)
    try {
      const result = await sessionsApi.deduct({ customer_id: selectedCustomer.id, branch_id: selectedBranch })
      toast.success(`เบิกเซสชันสำเร็จ — คงเหลือ ${result.remaining_hours} ชม.`)
      // Update remaining hours in-place (no full refetch)
      setSelectedCustomer((prev) => prev ? { ...prev, remaining_hours: result.remaining_hours } : null)
      // Reload history
      sessionsApi.log({ customer_id: selectedCustomer.id, page_size: 10, sort_by: 'created_at', sort_dir: 'desc' })
        .then((r) => setHistory(r.items)).catch(() => {})
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'เบิกเซสชันไม่สำเร็จ') : 'เบิกเซสชันไม่สำเร็จ')
    } finally {
      setIsDeducting(false)
    }
  }

  const historyColumns: TableColumn<SessionLogEntry>[] = [
    { key: 'created_at', label: 'เวลา',    render: (r) => <span className="text-body-sm">{r.created_at.slice(0, 16).replace('T', ' ')}</span> },
    { key: 'transaction_type', label: 'ประเภท', render: (r) => <span className="text-label-md font-medium">{r.transaction_type}</span> },
    { key: 'amount',    label: 'จำนวน',   render: (r) => <span className="tabular-nums">{r.amount > 0 ? `+${r.amount}` : r.amount}</span> },
    { key: 'after',     label: 'คงเหลือ', render: (r) => <span className="tabular-nums font-semibold text-tertiary">{r.after} ชม.</span> },
    { key: 'actor_name', label: 'โดย' },
  ]

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Branch chip selector (CR-02) */}
      {branches.length > 1 && (
        <div className="space-y-2">
          <p className="text-label-md text-on-surface font-medium">สาขา</p>
          <BranchChip branches={branches} selected={selectedBranch}
            onChange={setSelectedBranch}
            readOnly={user?.role !== 'owner' && user?.role !== 'developer'} />
        </div>
      )}

      {/* Customer search */}
      <div className="relative space-y-2">
        <p className="text-label-md text-on-surface font-medium">ค้นหาลูกค้า</p>
        <Input
          value={selectedCustomer ? `${selectedCustomer.display_name} (${selectedCustomer.code})` : customerSearch}
          onChange={(e) => { setCustomerSearch(e.target.value); setSelectedCustomer(null) }}
          placeholder="พิมพ์ชื่อหรือรหัส…"
          data-testid="session-deduct-customer-search"
        />
        {customerResults.length > 0 && !selectedCustomer && (
          <ul className="absolute z-10 left-0 right-0 mt-1 bg-surface-container-lowest border border-outline-variant rounded-lg shadow-elevated max-h-48 overflow-y-auto">
            {customerResults.map((c) => (
              <li key={c.id}>
                <button type="button"
                  className="w-full text-left px-3 py-2.5 hover:bg-surface-container-low transition-colors"
                  onClick={() => { setSelectedCustomer(c); setCustomerSearch(''); setCustomerResults([]) }}>
                  <span className="font-medium text-body-md">{c.display_name}</span>
                  <span className="ml-2 font-mono text-label-md text-secondary">({c.code})</span>
                  <span className={`ml-auto float-right font-semibold ${c.remaining_hours <= 0 ? 'text-error' : 'text-tertiary'}`}>
                    {c.remaining_hours} ชม.
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Selected customer summary + deduct button */}
      {selectedCustomer && (
        <div className="bg-surface-container-lowest rounded-xl p-6 shadow-ambient space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-title-md font-semibold text-on-surface">{selectedCustomer.display_name}</p>
              <span className="font-mono text-label-md text-secondary">{selectedCustomer.code}</span>
            </div>
            <div className="text-center px-4 py-2 rounded-xl border-2 border-tertiary/30 bg-tertiary/5 shrink-0">
              <p className={`text-display-sm font-display font-bold tabular-nums ${selectedCustomer.remaining_hours <= 0 ? 'text-error' : 'text-tertiary'}`}>
                {selectedCustomer.remaining_hours}
              </p>
              <p className="text-label-sm text-on-surface-variant">เซสชันคงเหลือ</p>
            </div>
          </div>

          <Button
            variant="primary"
            size="lg"
            className="w-full"
            onClick={handleDeduct}
            isLoading={isDeducting}
            disabled={selectedCustomer.remaining_hours <= 0}
            data-testid="session-deduct-btn"
          >
            {selectedCustomer.remaining_hours <= 0 ? 'เซสชันหมดแล้ว' : 'เบิกเซสชัน (−1 ชม.)'}
          </Button>
        </div>
      )}

      {/* Recent deduction history */}
      {selectedCustomer && (
        <div className="space-y-2">
          <p className="text-title-sm font-semibold text-on-surface">ประวัติล่าสุด</p>
          <Table columns={historyColumns} data={history} isLoading={isLoadingHistory}
            emptyMessage="ยังไม่มีประวัติ" rowKey={(r) => r.id} />
        </div>
      )}
    </div>
  )
}
