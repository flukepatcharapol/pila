// =============================================================================
// pages/customers/CustomerForm.tsx — Create / Edit customer (dual-mode)
// Mode is determined by the presence of :id in the URL.
//   /customers/new       → create mode (empty form)
//   /customers/:id/edit  → edit mode (pre-filled from GET /customers/:id)
//
// Sections: Branch + Source, Assignment, Identity, Contact, Status + Notes
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { customersApi } from '@/api/customers'
import { branchesApi } from '@/api/branches'
import { trainersApi } from '@/api/trainers'
import { caretakersApi } from '@/api/caretakers'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { ApiError } from '@/api/client'
import type { Customer, Branch, SourceType, Trainer, Caretaker } from '@/types'

// ---------------------------------------------------------------------------
// Form state shape
// ---------------------------------------------------------------------------

interface FormState {
  branch_id: string
  source_type_code: string
  trainer_id: string
  caretaker_id: string
  first_name: string
  last_name: string
  nickname: string
  phone: string
  line_id: string
  email: string
  birthday: string
  status: 'active' | 'inactive'
  notes: string
  is_duplicate: boolean
}

const EMPTY_FORM: FormState = {
  branch_id: '',
  source_type_code: '',
  trainer_id: '',
  caretaker_id: '',
  first_name: '',
  last_name: '',
  nickname: '',
  phone: '',
  line_id: '',
  email: '',
  birthday: '',
  status: 'active',
  notes: '',
  is_duplicate: false,
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CustomerForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  usePageTitle(isEdit ? 'แก้ไขลูกค้า' : 'เพิ่มลูกค้า')

  const navigate = useNavigate()
  const { toast } = useToast()
  const { activeBranchId, user } = useAuth()

  const [form, setForm]           = useState<FormState>(EMPTY_FORM)
  const [errors, setErrors]       = useState<Partial<Record<keyof FormState, string>>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(isEdit)

  // Reference data for dropdowns
  const [branches, setBranches]       = useState<Branch[]>([])
  const [sourceTypes, setSourceTypes] = useState<SourceType[]>([])
  const [trainers, setTrainers]       = useState<Trainer[]>([])
  const [caretakers, setCaretakers]   = useState<Caretaker[]>([])

  // Effective branch — from form state (or activeBranchId as default)
  const effectiveBranchId = form.branch_id || activeBranchId || ''

  // Load branches once on mount
  useEffect(() => {
    branchesApi.list().then(setBranches).catch(() => {})
  }, [])

  // Load source types, trainers, caretakers whenever effectiveBranchId changes
  useEffect(() => {
    if (!effectiveBranchId) return
    branchesApi.getSourceTypes(effectiveBranchId).then(setSourceTypes).catch(() => {})
    trainersApi.list({ branch_id: effectiveBranchId, status: 'active', page_size: 100 })
      .then((r) => setTrainers(r.items)).catch(() => {})
    caretakersApi.list({ branch_id: effectiveBranchId, status: 'active', page_size: 100 })
      .then((r) => setCaretakers(r.items)).catch(() => {})
  }, [effectiveBranchId])

  // Pre-fill form when editing — fetch customer data
  useEffect(() => {
    if (!isEdit || !id) return
    setIsFetching(true)
    customersApi.get(id)
      .then((c: Customer) => {
        setForm({
          branch_id:         c.branch_id,
          source_type_code:  '',   // not returned from GET; leave blank
          trainer_id:        c.trainer_id ?? '',
          caretaker_id:      c.caretaker_id ?? '',
          first_name:        c.first_name,
          last_name:         c.last_name,
          nickname:          c.nickname ?? '',
          phone:             c.phone ?? '',
          line_id:           c.line_id ?? '',
          email:             c.email ?? '',
          birthday:          c.birthday ?? '',
          status:            c.status,
          notes:             c.notes ?? '',
          is_duplicate:      c.is_duplicate,
        })
      })
      .catch(() => toast.error('โหลดข้อมูลลูกค้าไม่สำเร็จ'))
      .finally(() => setIsFetching(false))
  }, [id, isEdit])

  // Auto-fill branch_id when activeBranchId is available (create mode)
  useEffect(() => {
    if (!isEdit && activeBranchId && !form.branch_id) {
      setForm((prev) => ({ ...prev, branch_id: activeBranchId }))
    }
  }, [activeBranchId, isEdit])

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  function set(field: keyof FormState, value: string | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }))
    // Clear field error on change
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  function validate(): boolean {
    const e: Partial<Record<keyof FormState, string>> = {}
    if (!form.branch_id)  e.branch_id  = 'กรุณาเลือกสาขา'
    if (!form.first_name) e.first_name = 'กรุณากรอกชื่อ'
    if (!form.last_name)  e.last_name  = 'กรุณากรอกนามสกุล'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  // ---------------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------------

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    // Build the API payload — omit empty strings (treat as null on BE)
    const payload: Partial<Customer> = {
      branch_id:    form.branch_id,
      first_name:   form.first_name,
      last_name:    form.last_name,
      nickname:     form.nickname || undefined,
      phone:        form.phone    || undefined,
      line_id:      form.line_id  || undefined,
      email:        form.email    || undefined,
      birthday:     form.birthday || undefined,
      status:       form.status,
      notes:        form.notes    || undefined,
      is_duplicate: form.is_duplicate,
      trainer_id:   form.trainer_id   || undefined,
      caretaker_id: form.caretaker_id || undefined,
    }

    setIsLoading(true)
    try {
      if (isEdit && id) {
        await customersApi.update(id, payload)
        toast.success('บันทึกการแก้ไขสำเร็จ')
      } else {
        await customersApi.create(payload)
        toast.success('เพิ่มลูกค้าสำเร็จ')
      }
      navigate('/customers')
    } catch (err) {
      const msg = err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (isFetching) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const branchOptions = branches.map((b) => ({ value: b.id, label: b.name }))
  const sourceOptions = sourceTypes.map((s) => ({ value: s.code, label: `${s.label} (${s.code})` }))
  const trainerOptions = [
    { value: '', label: '— ไม่ระบุ —' },
    ...trainers.map((t) => ({ value: t.id, label: t.display_name })),
  ]
  const caretakerOptions = [
    { value: '', label: '— ไม่ระบุ —' },
    ...caretakers.map((c) => ({ value: c.id, label: c.name })),
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-2xl">
      {/* ── Back button ── */}
      <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/customers')}>
        ← กลับ
      </Button>

      <h2 className="text-headline-sm font-display font-bold text-on-surface">
        {isEdit ? 'แก้ไขลูกค้า' : 'เพิ่มลูกค้าใหม่'}
      </h2>

      {/* ── Section 1: Branch + Source ── */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">สาขาและแหล่งที่มา</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="สาขา"
            options={branchOptions}
            value={form.branch_id}
            onChange={(e) => set('branch_id', e.target.value)}
            error={errors.branch_id}
            required
            disabled={user?.role === 'admin' || user?.role === 'trainer'}
            data-testid="customer-form-branch"
          />
          <Select
            label="แหล่งที่มา"
            options={[{ value: '', label: '— ไม่ระบุ —' }, ...sourceOptions]}
            value={form.source_type_code}
            onChange={(e) => set('source_type_code', e.target.value)}
            data-testid="customer-form-source"
          />
        </div>
      </section>

      {/* ── Section 2: Assignment ── */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">การมอบหมาย</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="เทรนเนอร์"
            options={trainerOptions}
            value={form.trainer_id}
            onChange={(e) => set('trainer_id', e.target.value)}
            data-testid="customer-form-trainer"
          />
          <Select
            label="ผู้ดูแลเด็ก"
            options={caretakerOptions}
            value={form.caretaker_id}
            onChange={(e) => set('caretaker_id', e.target.value)}
            data-testid="customer-form-caretaker"
          />
        </div>
      </section>

      {/* ── Section 3: Identity ── */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">ข้อมูลส่วนตัว</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="ชื่อ"
            value={form.first_name}
            onChange={(e) => set('first_name', e.target.value)}
            error={errors.first_name}
            required
            data-testid="customer-form-first-name"
          />
          <Input
            label="นามสกุล"
            value={form.last_name}
            onChange={(e) => set('last_name', e.target.value)}
            error={errors.last_name}
            required
            data-testid="customer-form-last-name"
          />
          <Input
            label="ชื่อเล่น"
            value={form.nickname}
            onChange={(e) => set('nickname', e.target.value)}
            data-testid="customer-form-nickname"
          />
          <Input
            label="วันเกิด"
            type="date"
            value={form.birthday}
            onChange={(e) => set('birthday', e.target.value)}
            data-testid="customer-form-birthday"
          />
        </div>
      </section>

      {/* ── Section 4: Contact ── */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">ช่องทางติดต่อ</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="เบอร์โทรศัพท์"
            type="tel"
            value={form.phone}
            onChange={(e) => set('phone', e.target.value)}
            data-testid="customer-form-phone"
          />
          <Input
            label="LINE ID"
            value={form.line_id}
            onChange={(e) => set('line_id', e.target.value)}
            data-testid="customer-form-line-id"
          />
          <Input
            label="อีเมล"
            type="email"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
            data-testid="customer-form-email"
            className="sm:col-span-2"
          />
        </div>
      </section>

      {/* ── Section 5: Status + Notes ── */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">สถานะและหมายเหตุ</h3>
        <Select
          label="สถานะ"
          options={[
            { value: 'active',   label: 'ใช้งาน' },
            { value: 'inactive', label: 'ระงับ' },
          ]}
          value={form.status}
          onChange={(e) => set('status', e.target.value as 'active' | 'inactive')}
          data-testid="customer-form-status"
        />
        <div className="flex flex-col gap-1">
          <label className="text-label-md text-on-surface font-medium">หมายเหตุ</label>
          <textarea
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 rounded-md text-body-md text-on-surface bg-surface-container-lowest border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary outline-none transition-colors resize-none leading-thai"
            data-testid="customer-form-notes"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_duplicate}
            onChange={(e) => set('is_duplicate', e.target.checked)}
            className="form-checkbox rounded border-outline-variant text-secondary"
            data-testid="customer-form-duplicate"
          />
          <span className="text-body-md text-on-surface leading-thai">
            ทำเครื่องหมายว่าเป็นรายการซ้ำ (ต้องตรวจสอบ)
          </span>
        </label>
      </section>

      {/* ── Submit ── */}
      <div className="flex gap-3">
        <Button type="submit" variant="primary" isLoading={isLoading} data-testid="customer-form-submit">
          {isEdit ? 'บันทึกการแก้ไข' : 'เพิ่มลูกค้า'}
        </Button>
        <Button type="button" variant="ghost" onClick={() => navigate('/customers')}>
          ยกเลิก
        </Button>
      </div>
    </form>
  )
}
