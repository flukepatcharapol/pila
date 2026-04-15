// =============================================================================
// pages/sessions/TrainerReport.tsx — Training hours summary by trainer
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { sessionsApi } from '@/api/sessions'
import { DatePicker } from '@/components/ui/DatePicker'
import { Button } from '@/components/ui/Button'
import { StatCard } from '@/components/dashboard/StatCard'

interface TrainerReportEntry {
  trainer_id: string
  trainer_name: string
  total_hours: number
  session_count: number
}

export default function TrainerReport() {
  usePageTitle('รายงานเทรนเนอร์')

  const today      = new Date().toISOString().slice(0, 10)
  const firstOfMonth = today.slice(0, 7) + '-01'

  const [startDate, setStartDate] = useState<string | null>(firstOfMonth)
  const [endDate, setEndDate]     = useState<string | null>(today)
  const [data, setData]           = useState<TrainerReportEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)

  function fetchReport() {
    if (!startDate || !endDate) return
    setIsLoading(true)
    sessionsApi.trainerReport({ start_date: startDate, end_date: endDate })
      .then((r) => setData(r as unknown as TrainerReportEntry[]))
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }

  useEffect(() => { fetchReport() }, [])

  const totalHours    = data.reduce((s, r) => s + r.total_hours, 0)
  const totalSessions = data.reduce((s, r) => s + r.session_count, 0)

  return (
    <div className="space-y-6">
      {/* Date range filter */}
      <div className="flex flex-wrap items-end gap-4 p-4 rounded-xl bg-surface-container-low border border-outline-variant">
        <DatePicker label="ตั้งแต่" value={startDate} onChange={setStartDate} max={endDate ?? undefined} />
        <DatePicker label="ถึง"     value={endDate}   onChange={setEndDate}   min={startDate ?? undefined} />
        <Button variant="primary" onClick={fetchReport} isLoading={isLoading} data-testid="trainer-report-fetch-btn">
          ดูรายงาน
        </Button>
        {/* Quick presets */}
        <button type="button" className="text-label-md text-secondary hover:underline"
          onClick={() => { setStartDate(today); setEndDate(today) }}>วันนี้</button>
        <button type="button" className="text-label-md text-secondary hover:underline"
          onClick={() => { setStartDate(firstOfMonth); setEndDate(today) }}>เดือนนี้</button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard label="ชั่วโมงรวม" value={totalHours} unit="ชม."
          iconPath="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        <StatCard label="เซสชันรวม" value={totalSessions}
          iconPath="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </div>

      {/* Per-trainer breakdown */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center h-32 rounded-xl border border-outline-variant bg-surface-container-low">
          <p className="text-body-md text-on-surface-variant">ไม่พบข้อมูลในช่วงที่เลือก</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((entry) => (
            <div key={entry.trainer_id} className="bg-surface-container-lowest rounded-xl p-4 shadow-ambient">
              <p className="text-title-sm font-semibold text-on-surface">{entry.trainer_name}</p>
              <div className="mt-2 flex gap-6">
                <div>
                  <p className="text-display-sm font-display font-bold text-tertiary tabular-nums">{entry.total_hours}</p>
                  <p className="text-label-sm text-on-surface-variant">ชั่วโมง</p>
                </div>
                <div>
                  <p className="text-display-sm font-display font-bold text-secondary tabular-nums">{entry.session_count}</p>
                  <p className="text-label-sm text-on-surface-variant">เซสชัน</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
