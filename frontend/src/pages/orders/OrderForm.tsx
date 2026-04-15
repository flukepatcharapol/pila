// =============================================================================
// pages/orders/OrderForm.tsx — Create / Edit order (dual-mode)
// Handles customer search, package selection, payment method, and price calc.
// =============================================================================

import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { ordersApi } from '@/api/orders'
import { customersApi } from '@/api/customers'
import { packagesApi } from '@/api/packages'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { DatePicker } from '@/components/ui/DatePicker'
import { ApiError } from '@/api/client'
import type { Customer, Package, PaymentMethod } from '@/types'

interface FormState {
  order_date: string
  customer_id: string
  package_id: string
  hours: number
  bonus_hours: number
  price: number
  payment_method: PaymentMethod
  initial_payment: number
  trainer_id: string
  caretaker_id: string
  is_renewal: boolean
  notes: string
}

export default function OrderForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  usePageTitle(isEdit ? 'แก้ไขคำสั่งซื้อ' : 'คำสั่งซื้อใหม่')

  const navigate = useNavigate()
  const { toast } = useToast()
  const { activeBranchId } = useAuth()

  const today = new Date().toISOString().slice(0, 10)

  const [form, setForm] = useState<FormState>({
    order_date: today, customer_id: '', package_id: '',
    hours: 0, bonus_hours: 0, price: 0, payment_method: 'cash',
    initial_payment: 0, trainer_id: '', caretaker_id: '',
    is_renewal: false, notes: '',
  })
  const [errors, setErrors]           = useState<Partial<Record<keyof FormState, string>>>({})
  const [isLoading, setIsLoading]     = useState(false)
  const [isFetching, setIsFetching]   = useState(isEdit)

  // Customer search
  const [customerSearch, setCustomerSearch] = useState('')
  const [customerResults, setCustomerResults] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)

  // Packages list
  const [packages, setPackages] = useState<Package[]>([])

  // Derived values
  const totalHours = form.hours + form.bonus_hours
  const pricePerSession = totalHours > 0 ? Math.round(form.price / totalHours) : 0
  const outstanding = form.price - form.initial_payment

  // Load active packages for the branch
  useEffect(() => {
    packagesApi.list({ active_only: true, branch_id: activeBranchId ?? undefined, page_size: 100 })
      .then((r) => setPackages(r.items)).catch(() => {})
  }, [activeBranchId])

  // Debounced customer search
  useEffect(() => {
    if (customerSearch.length < 2) { setCustomerResults([]); return }
    const timer = setTimeout(() => {
      customersApi.list({ search: customerSearch, page_size: 8 })
        .then((r) => setCustomerResults(r.items)).catch(() => {})
    }, 300)
    return () => clearTimeout(timer)
  }, [customerSearch])

  // Pre-fill when editing
  useEffect(() => {
    if (!isEdit || !id) return
    setIsFetching(true)
    ordersApi.get(id).then((o) => {
      setForm({
        order_date:       o.order_date,
        customer_id:      o.customer_id,
        package_id:       o.package_id,
        hours:            o.hours,
        bonus_hours:      o.bonus_hours,
        price:            o.price,
        payment_method:   o.payments[0]?.method ?? 'cash',
        initial_payment:  o.payments.reduce((s, p) => s + p.amount, 0),
        trainer_id:       o.trainer_id ?? '',
        caretaker_id:     o.caretaker_id ?? '',
        is_renewal:       o.is_renewal,
        notes:            o.notes ?? '',
      })
      setSelectedCustomer({ display_name: o.customer_name, code: o.customer_code } as Customer)
    }).catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ'))
      .finally(() => setIsFetching(false))
  }, [id, isEdit])

  // Auto-fill hours/price when package is selected
  function handlePackageChange(pkgId: string) {
    const pkg = packages.find((p) => p.id === pkgId)
    if (pkg) {
      setForm((prev) => ({ ...prev, package_id: pkgId, hours: pkg.hours, price: pkg.price }))
    } else {
      setForm((prev) => ({ ...prev, package_id: pkgId }))
    }
  }

  const set = useCallback((field: keyof FormState, value: string | number | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
  }, [])

  function validate() {
    const e: Partial<Record<keyof FormState, string>> = {}
    if (!form.customer_id)  e.customer_id  = 'กรุณาเลือกลูกค้า'
    if (!form.package_id)   e.package_id   = 'กรุณาเลือกแพ็กเกจ'
    if (!form.order_date)   e.order_date   = 'กรุณาเลือกวันที่'
    if (form.price <= 0)    e.price        = 'กรุณากรอกราคา'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setIsLoading(true)
    try {
      const payload = {
        order_date:    form.order_date,
        customer_id:   form.customer_id,
        package_id:    form.package_id,
        hours:         form.hours,
        bonus_hours:   form.bonus_hours,
        price:         form.price,
        trainer_id:    form.trainer_id   || undefined,
        caretaker_id:  form.caretaker_id || undefined,
        is_renewal:    form.is_renewal,
        notes:         form.notes        || undefined,
      }
      if (isEdit && id) {
        await ordersApi.update(id, payload)
        toast.success('บันทึกการแก้ไขสำเร็จ')
      } else {
        await ordersApi.create(payload)
        toast.success('สร้างคำสั่งซื้อสำเร็จ')
      }
      navigate('/orders')
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally {
      setIsLoading(false)
    }
  }

  if (isFetching) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>

  const packageOptions = [
    { value: '', label: '— เลือกแพ็กเกจ —' },
    ...packages.map((p) => ({ value: p.id, label: `${p.name} (${p.hours} ชม. / ${p.price.toLocaleString()} ฿)` })),
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/orders')}>← กลับ</Button>
      <h2 className="text-headline-sm font-display font-bold text-on-surface">{isEdit ? 'แก้ไขคำสั่งซื้อ' : 'คำสั่งซื้อใหม่'}</h2>

      {/* Date + Customer */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">ข้อมูลทั่วไป</h3>
        <DatePicker label="วันที่" value={form.order_date} onChange={(v) => set('order_date', v ?? '')} required />

        {/* Customer search — shows Name (Code) per CR-01 */}
        <div className="relative">
          <Input label="ลูกค้า" value={selectedCustomer ? `${selectedCustomer.display_name} (${selectedCustomer.code})` : customerSearch}
            onChange={(e) => { setCustomerSearch(e.target.value); setSelectedCustomer(null); set('customer_id', '') }}
            error={errors.customer_id} placeholder="พิมพ์ชื่อหรือรหัสเพื่อค้นหา…" required data-testid="order-form-customer" />
          {customerResults.length > 0 && !selectedCustomer && (
            <ul className="absolute z-10 top-full left-0 right-0 mt-1 bg-surface-container-lowest border border-outline-variant rounded-lg shadow-elevated max-h-48 overflow-y-auto">
              {customerResults.map((c) => (
                <li key={c.id}>
                  <button type="button" className="w-full text-left px-3 py-2 text-body-md hover:bg-surface-container-low transition-colors"
                    onClick={() => { setSelectedCustomer(c); set('customer_id', c.id); setCustomerSearch(''); setCustomerResults([]) }}>
                    <span className="font-medium">{c.display_name}</span>
                    <span className="ml-2 font-mono text-label-md text-secondary">({c.code})</span>
                    <span className="ml-2 text-body-sm text-on-surface-variant">{c.remaining_hours} ชม.</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Package + Hours */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">แพ็กเกจและชั่วโมง</h3>
        <Select label="แพ็กเกจ" options={packageOptions} value={form.package_id}
          onChange={(e) => handlePackageChange(e.target.value)} error={errors.package_id} required data-testid="order-form-package" />
        <div className="grid grid-cols-2 gap-4">
          <Input label="ชั่วโมงหลัก" type="number" min="0" value={String(form.hours)} onChange={(e) => set('hours', Number(e.target.value))} />
          <Input label="ชั่วโมงโบนัส" type="number" min="0" value={String(form.bonus_hours)} onChange={(e) => set('bonus_hours', Number(e.target.value))} />
        </div>
        <div className="flex gap-6 text-body-sm text-on-surface-variant">
          <span>รวม: <strong className="text-on-surface">{totalHours} ชม.</strong></span>
          <span>ราคา/เซสชัน: <strong className="text-on-surface">{pricePerSession.toLocaleString()} ฿</strong></span>
        </div>
      </section>

      {/* Payment */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">การชำระเงิน</h3>
        <div className="grid grid-cols-2 gap-4">
          <Input label="ราคารวม (฿)" type="number" min="0" value={String(form.price)} onChange={(e) => set('price', Number(e.target.value))} error={errors.price} required />
          <Input label="ชำระแล้ว (฿)" type="number" min="0" value={String(form.initial_payment)} onChange={(e) => set('initial_payment', Number(e.target.value))} />
        </div>
        <Select label="วิธีชำระ" options={[{ value: 'cash', label: 'เงินสด' }, { value: 'bank_transfer', label: 'โอนเงิน' }, { value: 'credit', label: 'บัตรเครดิต' }]}
          value={form.payment_method} onChange={(e) => set('payment_method', e.target.value as PaymentMethod)} />
        <p className="text-body-sm text-on-surface-variant">ค้างชำระ: <strong className={outstanding > 0 ? 'text-error' : 'text-tertiary'}>{outstanding.toLocaleString()} ฿</strong></p>
      </section>

      {/* Notes + flags */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">หมายเหตุ</h3>
        <textarea value={form.notes} onChange={(e) => set('notes', e.target.value)} rows={3}
          className="w-full px-3 py-2 rounded-md text-body-md border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary outline-none resize-none leading-thai bg-surface-container-lowest" />
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={form.is_renewal} onChange={(e) => set('is_renewal', e.target.checked)} className="form-checkbox rounded border-outline-variant text-secondary" />
          <span className="text-body-md text-on-surface leading-thai">การต่ออายุ (Renewal)</span>
        </label>
      </section>

      <div className="flex gap-3">
        <Button type="submit" variant="primary" isLoading={isLoading} data-testid="order-form-submit">{isEdit ? 'บันทึก' : 'สร้างคำสั่งซื้อ'}</Button>
        <Button type="button" variant="ghost" onClick={() => navigate('/orders')}>ยกเลิก</Button>
      </div>
    </form>
  )
}
