// =============================================================================
// components/booking/BookingPopup.tsx — Modal form to create/view a booking
// Pre-fills date/time from the clicked timetable slot.
// =============================================================================

import { useState, useEffect } from 'react'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { bookingsApi } from '@/api/bookings'
import { customersApi } from '@/api/customers'
import { trainersApi } from '@/api/trainers'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { ApiError } from '@/api/client'
import type { Customer, Trainer, Booking } from '@/types'

interface BookingPopupProps {
  isOpen: boolean
  onClose: () => void
  onSaved: () => void
  // Pre-filled from timetable slot click
  prefillDate?: string   // "YYYY-MM-DD"
  prefillSlot?: number   // slot index (0 = 08:00)
  // If provided, viewing an existing booking (read-only + confirm/cancel actions)
  existingBooking?: Booking | null
}

const SLOT_START_HOUR = 8
const SLOT_MINS       = 30

function slotToTime(slot: number): string {
  const totalMin = SLOT_START_HOUR * 60 + slot * SLOT_MINS
  const h = Math.floor(totalMin / 60)
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

export function BookingPopup({ isOpen, onClose, onSaved, prefillDate, prefillSlot, existingBooking }: BookingPopupProps) {
  const { toast } = useToast()
  const { activeBranchId } = useAuth()

  const [customerSearch, setCustomerSearch]   = useState('')
  const [customerResults, setCustomerResults] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [trainerId, setTrainerId]             = useState('')
  const [trainers, setTrainers]               = useState<Trainer[]>([])
  const [date, setDate]                       = useState(prefillDate ?? '')
  const [startTime, setStartTime]             = useState(prefillSlot !== undefined ? slotToTime(prefillSlot) : '09:00')
  const [durationSlots, setDurationSlots]     = useState(2)  // default 1 hour = 2 slots
  const [notes, setNotes]                     = useState('')
  const [isSaving, setIsSaving]               = useState(false)
  const [isConfirming, setIsConfirming]       = useState(false)

  const isViewMode = Boolean(existingBooking)

  // Load trainers for dropdown
  useEffect(() => {
    if (!isOpen) return
    trainersApi.list({ branch_id: activeBranchId ?? undefined, status: 'active', page_size: 100 })
      .then((r) => setTrainers(r.items)).catch(() => {})
  }, [isOpen, activeBranchId])

  // Pre-fill from existing booking
  useEffect(() => {
    if (!existingBooking) return
    setDate(existingBooking.start_at.slice(0, 10))
    setStartTime(existingBooking.start_at.slice(11, 16))
    setTrainerId(existingBooking.trainer_id)
    setNotes(existingBooking.notes ?? '')
    setSelectedCustomer({ display_name: existingBooking.customer_name } as Customer)
  }, [existingBooking])

  // Reset on close
  useEffect(() => {
    if (!isOpen) {
      setCustomerSearch(''); setCustomerResults([]); setSelectedCustomer(null)
      setTrainerId(''); setNotes(''); setIsSaving(false)
    }
  }, [isOpen])

  useEffect(() => {
    if (customerSearch.length < 2) { setCustomerResults([]); return }
    const t = setTimeout(() => {
      customersApi.list({ search: customerSearch, branch_id: activeBranchId ?? undefined, page_size: 8 })
        .then((r) => setCustomerResults(r.items)).catch(() => {})
    }, 300)
    return () => clearTimeout(t)
  }, [customerSearch, activeBranchId])

  async function handleSave() {
    if (!selectedCustomer || !trainerId || !date || !startTime) { toast.error('กรุณากรอกข้อมูลให้ครบ'); return }
    setIsSaving(true)
    try {
      const [h, m] = startTime.split(':').map(Number)
      const startDate = new Date(`${date}T${startTime}:00`)
      const endDate   = new Date(startDate.getTime() + durationSlots * SLOT_MINS * 60 * 1000)
      const fmt = (d: Date) => d.toISOString()
      await bookingsApi.create({
        customer_id: selectedCustomer.id,
        trainer_id:  trainerId,
        start_at:    fmt(startDate),
        end_at:      fmt(endDate),
        branch_id:   activeBranchId ?? '',
        notes:       notes || undefined,
      })
      toast.success('สร้างการจองสำเร็จ')
      onSaved(); onClose()
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'สร้างการจองไม่สำเร็จ') : 'สร้างการจองไม่สำเร็จ')
    } finally { setIsSaving(false) }
  }

  async function handleConfirm() {
    if (!existingBooking) return
    setIsConfirming(true)
    try {
      await bookingsApi.confirm(existingBooking.id)
      toast.success('ยืนยันการจองสำเร็จ')
      onSaved(); onClose()
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'ยืนยันไม่สำเร็จ') : 'ยืนยันไม่สำเร็จ')
    } finally { setIsConfirming(false) }
  }

  async function handleCancel() {
    if (!existingBooking) return
    try {
      await bookingsApi.cancel(existingBooking.id)
      toast.success('ยกเลิกการจองแล้ว')
      onSaved(); onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ยกเลิกไม่สำเร็จ')
    }
  }

  const trainerOptions = [{ value: '', label: '— เลือกเทรนเนอร์ —' }, ...trainers.map((t) => ({ value: t.id, label: t.display_name }))]
  const durationOptions = [1, 2, 3, 4, 6, 8].map((s) => ({ value: String(s), label: `${s * SLOT_MINS} นาที (${s} slots)` }))

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isViewMode ? 'รายละเอียดการจอง' : 'จองการฝึก'} size="md"
      footer={
        isViewMode ? (
          <div className="flex gap-2 w-full flex-wrap">
            {existingBooking?.status === 'pending' && (
              <Button variant="primary" onClick={handleConfirm} isLoading={isConfirming} data-testid="booking-confirm-btn">ยืนยันการจอง</Button>
            )}
            {existingBooking?.status !== 'cancelled' && (
              <Button variant="danger" onClick={handleCancel} data-testid="booking-cancel-btn">ยกเลิกการจอง</Button>
            )}
            <Button variant="ghost" onClick={onClose} className="ml-auto">ปิด</Button>
          </div>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose}>ยกเลิก</Button>
            <Button variant="primary" onClick={handleSave} isLoading={isSaving} data-testid="booking-save-btn">จอง</Button>
          </>
        )
      }
    >
      <div className="space-y-4">
        {/* Customer picker */}
        {!isViewMode ? (
          <div className="relative">
            <Input label="ลูกค้า" value={selectedCustomer ? `${selectedCustomer.display_name}` : customerSearch}
              onChange={(e) => { setCustomerSearch(e.target.value); setSelectedCustomer(null) }}
              placeholder="ค้นหาลูกค้า…" required data-testid="booking-customer-search" />
            {customerResults.length > 0 && !selectedCustomer && (
              <ul className="absolute z-10 left-0 right-0 mt-1 bg-surface-container-lowest border border-outline-variant rounded-lg shadow-elevated max-h-40 overflow-y-auto">
                {customerResults.map((c) => (
                  <li key={c.id}>
                    <button type="button" className="w-full text-left px-3 py-2 text-body-md hover:bg-surface-container-low"
                      onClick={() => { setSelectedCustomer(c); setCustomerSearch(''); setCustomerResults([]) }}>
                      {c.display_name} <span className="text-secondary font-mono text-label-md">({c.code})</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <div><p className="text-label-md text-on-surface-variant">ลูกค้า</p><p className="text-body-md font-medium">{existingBooking?.customer_name}</p></div>
        )}

        <Select label="เทรนเนอร์" options={trainerOptions} value={trainerId} onChange={(e) => setTrainerId(e.target.value)} required disabled={isViewMode} />

        <div className="grid grid-cols-2 gap-4">
          <Input label="วันที่" type="date" value={date} onChange={(e) => setDate(e.target.value)} required disabled={isViewMode} />
          <Input label="เวลาเริ่ม" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} required disabled={isViewMode} />
        </div>

        {!isViewMode && (
          <Select label="ระยะเวลา" options={durationOptions} value={String(durationSlots)} onChange={(e) => setDurationSlots(Number(e.target.value))} />
        )}

        <div className="flex flex-col gap-1">
          <label className="text-label-md font-medium text-on-surface">หมายเหตุ</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} disabled={isViewMode}
            className="w-full px-3 py-2 rounded-md text-body-md border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary outline-none resize-none bg-surface-container-lowest leading-thai disabled:bg-surface-container-high" />
        </div>
      </div>
    </Modal>
  )
}

export default BookingPopup
