// =============================================================================
// pages/booking/BookingSchedule.tsx — Booking timetable + table view toggle
// Displays a 3-day or 7-day timetable grid of bookings.
// =============================================================================

import { useState, useEffect, useCallback } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { bookingsApi } from '@/api/bookings'
import { useAuth } from '@/stores/AuthContext'
import { TimetableGrid } from '@/components/booking/TimetableGrid'
import { BookingPopup } from '@/components/booking/BookingPopup'
import { Button } from '@/components/ui/Button'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { useTable } from '@/hooks/useTable'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import type { Booking } from '@/types'

type ViewMode = '3day' | '7day' | 'table'

export default function BookingSchedule() {
  usePageTitle('ตารางจอง')
  const { activeBranchId } = useAuth()

  const [viewMode, setViewMode]           = useState<ViewMode>('3day')
  const [anchorDate, setAnchorDate]       = useState(new Date())
  const [timetableBookings, setTimetableBookings] = useState<Booking[]>([])
  const [isFetching, setIsFetching]       = useState(false)

  // Popup state
  const [popupOpen, setPopupOpen]         = useState(false)
  const [prefillDate, setPrefillDate]     = useState<string | undefined>()
  const [prefillSlot, setPrefillSlot]     = useState<number | undefined>()
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null)

  // Table view data
  const { data: tableData, total, isLoading: tableLoading, params, setPage } = useTable(bookingsApi.list)

  // Generate displayed dates from anchor
  const numDays = viewMode === '7day' ? 7 : 3
  const dates = Array.from({ length: numDays }, (_, i) => {
    const d = new Date(anchorDate)
    d.setDate(d.getDate() + i)
    return d
  })

  // Navigate backward/forward
  function navigate(direction: 'prev' | 'next') {
    const d = new Date(anchorDate)
    d.setDate(d.getDate() + (direction === 'next' ? numDays : -numDays))
    setAnchorDate(d)
  }

  // Fetch timetable bookings for the visible date range
  const fetchTimetable = useCallback(() => {
    if (viewMode === 'table') return
    setIsFetching(true)
    const start = dates[0].toISOString().slice(0, 10)
    const end   = dates[dates.length - 1].toISOString().slice(0, 10)
    bookingsApi.list({ start_date: start, end_date: end, branch_id: activeBranchId ?? undefined, page_size: 200 })
      .then((r) => setTimetableBookings(r.items))
      .catch(() => {})
      .finally(() => setIsFetching(false))
  }, [viewMode, anchorDate, activeBranchId])

  useEffect(() => { fetchTimetable() }, [fetchTimetable])

  function handleSlotClick(date: Date, slot: number) {
    setPrefillDate(date.toISOString().slice(0, 10))
    setPrefillSlot(slot)
    setSelectedBooking(null)
    setPopupOpen(true)
  }

  function handleBookingClick(booking: Booking) {
    setSelectedBooking(booking)
    setPrefillDate(undefined)
    setPrefillSlot(undefined)
    setPopupOpen(true)
  }

  function formatDateRange() {
    const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }
    const start = dates[0].toLocaleDateString('th-TH', opts)
    const end   = dates[dates.length - 1].toLocaleDateString('th-TH', opts)
    return `${start} – ${end}`
  }

  const tableColumns: TableColumn<Booking>[] = [
    { key: 'start_at',      label: 'วันเวลา',   render: (r) => <span className="text-body-sm">{r.start_at.slice(0, 16).replace('T', ' ')}</span> },
    { key: 'customer_name', label: 'ลูกค้า' },
    { key: 'trainer_name',  label: 'เทรนเนอร์' },
    { key: 'status',        label: 'สถานะ', render: (r) => <StatusBadge label={r.status} variant={resolveStatusVariant(r.status)} /> },
    {
      key: 'actions', label: '',
      render: (r) => (
        <div className="flex gap-2 justify-end">
          {r.status === 'pending' && (
            <Button variant="primary" size="sm" onClick={() => bookingsApi.confirm(r.id).then(fetchTimetable)} data-testid={`booking-confirm-${r.id}`}>ยืนยัน</Button>
          )}
          {r.status !== 'cancelled' && (
            <Button variant="danger" size="sm" onClick={() => bookingsApi.cancel(r.id).then(fetchTimetable)} data-testid={`booking-cancel-${r.id}`}>ยกเลิก</Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* View mode toggle */}
        <div className="flex rounded-lg border border-outline-variant overflow-hidden">
          {(['3day', '7day', 'table'] as ViewMode[]).map((v) => (
            <button key={v} type="button" onClick={() => setViewMode(v)}
              className={`px-3 py-1.5 text-label-md transition-colors ${viewMode === v ? 'bg-secondary text-on-secondary' : 'text-on-surface-variant hover:bg-surface-container-low'}`}>
              {v === '3day' ? '3 วัน' : v === '7day' ? '7 วัน' : 'รายการ'}
            </button>
          ))}
        </div>

        {/* Date navigation (timetable modes only) */}
        {viewMode !== 'table' && (
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => navigate('prev')} className="p-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low transition-colors" aria-label="ก่อนหน้า">‹</button>
            <span className="text-body-md font-medium text-on-surface min-w-[140px] text-center">{formatDateRange()}</span>
            <button type="button" onClick={() => navigate('next')} className="p-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low transition-colors" aria-label="ถัดไป">›</button>
            <Button variant="ghost" size="sm" onClick={() => setAnchorDate(new Date())}>วันนี้</Button>
          </div>
        )}

        <Button variant="primary" size="sm" onClick={() => { setSelectedBooking(null); setPrefillDate(undefined); setPrefillSlot(undefined); setPopupOpen(true) }} data-testid="booking-add-btn">
          + จองใหม่
        </Button>
      </div>

      {/* Timetable or table view */}
      {viewMode !== 'table' ? (
        isFetching ? (
          <div className="h-96 rounded-xl bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer" />
        ) : (
          <TimetableGrid
            dates={dates}
            bookings={timetableBookings}
            onSlotClick={handleSlotClick}
            onBookingClick={handleBookingClick}
          />
        )
      ) : (
        <>
          <Table columns={tableColumns} data={tableData} isLoading={tableLoading} emptyMessage="ไม่พบการจอง" rowKey={(r) => r.id} />
          <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />
        </>
      )}

      {/* Booking popup */}
      <BookingPopup
        isOpen={popupOpen}
        onClose={() => setPopupOpen(false)}
        onSaved={fetchTimetable}
        prefillDate={prefillDate}
        prefillSlot={prefillSlot}
        existingBooking={selectedBooking}
      />
    </div>
  )
}
