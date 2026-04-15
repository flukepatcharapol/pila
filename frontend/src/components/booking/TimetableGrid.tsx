// =============================================================================
// components/booking/TimetableGrid.tsx — Visual timetable for bookings
// CSS Grid: columns = days, rows = 30-min slots from 08:00–22:00 (28 rows).
// Booked slots are positioned absolutely inside their day column.
// Clicking an empty slot opens the booking form popup.
// =============================================================================

import type { Booking } from '@/types'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const START_HOUR = 8    // 08:00
const END_HOUR   = 22   // 22:00
const SLOT_MINS  = 30   // 30-minute slots
const TOTAL_SLOTS = ((END_HOUR - START_HOUR) * 60) / SLOT_MINS  // 28 slots

// Colours per booking status
const STATUS_COLORS: Record<string, string> = {
  confirmed: 'bg-tertiary/80 text-on-tertiary border-tertiary',
  pending:   'bg-amber-400/80 text-amber-900 border-amber-500',
  cancelled: 'bg-surface-container-high text-on-surface-variant border-outline-variant line-through',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// Convert an ISO datetime string to minutes since START_HOUR (e.g. "2024-01-15T09:30:00" → 90)
function toMinutes(isoDateTime: string): number {
  const d = new Date(isoDateTime)
  return (d.getHours() - START_HOUR) * 60 + d.getMinutes()
}

// Format time slot label: slot 0 → "08:00", slot 3 → "09:30"
function slotLabel(slot: number): string {
  const totalMin = START_HOUR * 60 + slot * SLOT_MINS
  const h = Math.floor(totalMin / 60)
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Format column header: "จ 15/01" for date 2024-01-15
function dayLabel(date: Date): string {
  const thDays = ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส']
  const d = String(date.getDate()).padStart(2, '0')
  const m = String(date.getMonth() + 1).padStart(2, '0')
  return `${thDays[date.getDay()]} ${d}/${m}`
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TimetableGridProps {
  dates: Date[]          // array of days to display as columns
  bookings: Booking[]
  onSlotClick: (date: Date, slotIndex: number) => void
  onBookingClick: (booking: Booking) => void
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TimetableGrid({ dates, bookings, onSlotClick, onBookingClick }: TimetableGridProps) {
  // Group bookings by ISO date string "YYYY-MM-DD"
  const bookingsByDate: Record<string, Booking[]> = {}
  bookings.forEach((b) => {
    const dateKey = b.start_at.slice(0, 10)
    if (!bookingsByDate[dateKey]) bookingsByDate[dateKey] = []
    bookingsByDate[dateKey].push(b)
  })

  // Slot height in pixels — each 30-min slot is 48px tall
  const SLOT_HEIGHT = 48

  return (
    <div className="overflow-x-auto rounded-xl border border-outline-variant">
      <div
        className="grid min-w-max"
        style={{ gridTemplateColumns: `56px repeat(${dates.length}, minmax(140px, 1fr))` }}
      >
        {/* ── Header row: empty corner + day labels ── */}
        <div className="sticky left-0 bg-surface-container-low border-b border-r border-outline-variant" />
        {dates.map((date) => (
          <div
            key={date.toISOString()}
            className="px-2 py-2 text-label-md font-semibold text-on-surface text-center bg-surface-container-low border-b border-r border-outline-variant"
          >
            {dayLabel(date)}
          </div>
        ))}

        {/* ── Body: time labels + day columns ── */}
        {Array.from({ length: TOTAL_SLOTS }).map((_, slotIdx) => (
          <>
            {/* Time label — sticky left */}
            <div
              key={`label-${slotIdx}`}
              className="sticky left-0 z-10 flex items-start justify-end pr-2 pt-1 bg-surface-container-lowest border-r border-outline-variant text-label-sm text-on-surface-variant select-none"
              style={{ height: SLOT_HEIGHT }}
            >
              {/* Only show label on the hour (every 2 slots) */}
              {slotIdx % 2 === 0 && slotLabel(slotIdx)}
            </div>

            {/* Day columns for this slot row */}
            {dates.map((date) => {
              const dateKey = date.toISOString().slice(0, 10)
              return (
                <div
                  key={`${dateKey}-${slotIdx}`}
                  className="relative border-r border-b border-outline-variant/40 cursor-pointer hover:bg-secondary/5 transition-colors"
                  style={{ height: SLOT_HEIGHT }}
                  onClick={() => onSlotClick(date, slotIdx)}
                  data-testid={`timetable-slot-${dateKey}-${slotIdx}`}
                />
              )
            })}
          </>
        ))}

        {/* ── Booking overlays (absolutely positioned per day column) ── */}
        {/* We render a second pass of day columns to place booking blocks */}
        {dates.map((date, colIdx) => {
          const dateKey = date.toISOString().slice(0, 10)
          const dayBookings = bookingsByDate[dateKey] ?? []

          return dayBookings.map((booking) => {
            const startMin    = toMinutes(booking.start_at)
            const endMin      = toMinutes(booking.end_at)
            const durationMin = endMin - startMin
            const topPx   = (startMin / SLOT_MINS) * SLOT_HEIGHT + SLOT_HEIGHT // +1 row for header
            const heightPx = (durationMin / SLOT_MINS) * SLOT_HEIGHT

            // Column position: time label column is 1, days start at column 2
            const colStart = colIdx + 2  // 1-based CSS grid column

            return (
              <div
                key={booking.id}
                className={[
                  'absolute z-20 mx-0.5 rounded-md border text-label-sm font-medium px-1.5 py-1',
                  'overflow-hidden cursor-pointer hover:opacity-90 transition-opacity',
                  STATUS_COLORS[booking.status] ?? STATUS_COLORS.pending,
                ].join(' ')}
                style={{
                  gridColumn: colStart,
                  gridRow: 1,
                  top: topPx,
                  height: heightPx - 2,
                  // Each day column shares same grid column, so we need absolute positioning
                  // This is achieved by setting the parent grid to position:relative
                  left: 0,
                  right: 0,
                }}
                onClick={(e) => { e.stopPropagation(); onBookingClick(booking) }}
                title={`${booking.customer_name} — ${booking.trainer_name}`}
              >
                <p className="truncate">{booking.customer_name}</p>
                <p className="truncate opacity-75">{booking.trainer_name}</p>
              </div>
            )
          })
        })}
      </div>
    </div>
  )
}

export default TimetableGrid
