// =============================================================================
// pages/Dashboard.tsx — Main dashboard with role-based KPI metrics
// Replaces the previous skeleton. Fetches from GET /dashboard with a
// time-period filter. Owner/developer can also filter by branch.
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useAuth } from '@/stores/AuthContext'
import { dashboardApi, type DashboardPeriod } from '@/api/dashboard'
import { branchesApi } from '@/api/branches'
import { StatCard } from '@/components/dashboard/StatCard'
import { BranchChip } from '@/components/ui/BranchChip'
import { DatePicker } from '@/components/ui/DatePicker'
import type { DashboardData, Branch } from '@/types'

// ---------------------------------------------------------------------------
// Period toggle button
// ---------------------------------------------------------------------------

interface PeriodButtonProps {
  label: string
  value: DashboardPeriod
  active: boolean
  onClick: () => void
}

function PeriodButton({ label, value, active, onClick }: PeriodButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`dashboard-period-${value}`}
      className={[
        'px-4 py-1.5 rounded-lg text-label-md font-medium transition-all duration-150',
        active
          ? 'bg-secondary text-on-secondary shadow-ambient'
          : 'text-on-surface-variant hover:bg-surface-container-low',
      ].join(' ')}
    >
      {label}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Icon paths matched by metric label keyword
// ---------------------------------------------------------------------------

function resolveIcon(label: string): string {
  const l = label.toLowerCase()
  if (l.includes('hour') || l.includes('ชั่วโมง'))
    return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
  if (l.includes('order') || l.includes('คำสั่ง'))
    return 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'
  if (l.includes('revenue') || l.includes('รายได้') || l.includes('บาท'))
    return 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  if (l.includes('customer') || l.includes('ลูกค้า'))
    return 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z'
  if (l.includes('booking') || l.includes('การจอง'))
    return 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
  return 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

export default function Dashboard() {
  usePageTitle('Dashboard')

  const { user, activeBranchId } = useAuth()

  const [period, setPeriod]       = useState<DashboardPeriod>('today')
  const [startDate, setStartDate] = useState<string | null>(null)
  const [endDate, setEndDate]     = useState<string | null>(null)

  // Owner/developer can filter across branches; others are locked to their branch
  const canSwitchBranch = user?.role === 'owner' || user?.role === 'developer'
  const [filterBranchId, setFilterBranchId] = useState<string | null>(
    canSwitchBranch ? null : (activeBranchId ?? null),
  )
  const [branches, setBranches]   = useState<Branch[]>([])
  const [dashData, setDashData]   = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]         = useState<string | null>(null)

  // Load branch list for owner/developer switcher
  useEffect(() => {
    if (!canSwitchBranch) return
    branchesApi.list().then(setBranches).catch(() => {})
  }, [canSwitchBranch])

  // Fetch dashboard metrics whenever filters change
  useEffect(() => {
    if (period === 'custom' && (!startDate || !endDate)) return

    setIsLoading(true)
    setError(null)

    dashboardApi
      .get({
        period,
        branch_id:  filterBranchId ?? undefined,
        start_date: period === 'custom' ? startDate ?? undefined : undefined,
        end_date:   period === 'custom' ? endDate   ?? undefined : undefined,
      })
      .then((data) => { setDashData(data); setIsLoading(false) })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'โหลดข้อมูลไม่สำเร็จ')
        setIsLoading(false)
      })
  }, [period, startDate, endDate, filterBranchId])

  return (
    <div className="space-y-6">
      {/* ── Header + period selector ── */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-headline-sm font-display font-bold text-on-surface">
            สวัสดี, {user?.display_name ?? '—'} 👋
          </h2>
          <p className="text-body-md text-on-surface-variant leading-thai mt-0.5">
            ภาพรวมของสตูดิโอในช่วงเวลาที่เลือก
          </p>
        </div>

        <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-container-low border border-outline-variant flex-wrap">
          {([
            { value: 'today',  label: 'วันนี้' },
            { value: 'week',   label: 'สัปดาห์นี้' },
            { value: 'month',  label: 'เดือนนี้' },
            { value: 'custom', label: 'กำหนดเอง' },
          ] as { value: DashboardPeriod; label: string }[]).map((p) => (
            <PeriodButton
              key={p.value}
              value={p.value}
              label={p.label}
              active={period === p.value}
              onClick={() => setPeriod(p.value)}
            />
          ))}
        </div>
      </div>

      {/* Custom date range — shown only for 'กำหนดเอง' */}
      {period === 'custom' && (
        <div className="flex flex-wrap gap-4 p-4 rounded-xl bg-surface-container-low border border-outline-variant">
          <DatePicker label="ตั้งแต่วันที่" value={startDate} onChange={setStartDate} max={endDate ?? undefined} />
          <DatePicker label="ถึงวันที่"     value={endDate}   onChange={setEndDate}   min={startDate ?? undefined} />
        </div>
      )}

      {/* Branch filter chips — owner/developer only (CR-02) */}
      {canSwitchBranch && branches.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setFilterBranchId(null)}
            data-testid="dashboard-branch-all"
            className={[
              'px-3 py-1 rounded-full text-label-md font-medium border transition-all',
              filterBranchId === null
                ? 'bg-secondary text-on-secondary border-secondary'
                : 'bg-surface-container-low text-on-surface border-outline-variant hover:bg-surface-container',
            ].join(' ')}
          >
            ทุกสาขา
          </button>
          <BranchChip branches={branches} selected={filterBranchId} onChange={setFilterBranchId} />
        </div>
      )}

      {/* ── Metrics grid ── */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer" />
          ))}
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-40 rounded-xl border border-error/20 bg-error-container/10">
          <p className="text-body-md text-on-error-container leading-thai">{error}</p>
        </div>
      ) : dashData && dashData.metrics.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {dashData.metrics.map((metric) => (
            <StatCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              unit={metric.unit}
              trend={metric.trend}
              iconPath={resolveIcon(metric.label)}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-48 rounded-xl border border-outline-variant bg-surface-container-low">
          <p className="text-body-md text-on-surface-variant leading-thai">ไม่มีข้อมูลในช่วงที่เลือก</p>
        </div>
      )}
    </div>
  )
}
