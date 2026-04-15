// =============================================================================
// pages/packages/PackageForm.tsx — Create / Edit package
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { packagesApi } from '@/api/packages'
import { branchesApi } from '@/api/branches'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { DatePicker } from '@/components/ui/DatePicker'
import { ApiError } from '@/api/client'
import type { Branch, PackageType } from '@/types'

export default function PackageForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  usePageTitle(isEdit ? 'แก้ไขแพ็กเกจ' : 'เพิ่มแพ็กเกจ')
  const navigate = useNavigate()
  const { toast } = useToast()

  const [name, setName]             = useState('')
  const [hours, setHours]           = useState(10)
  const [type, setType]             = useState<PackageType>('sale')
  const [price, setPrice]           = useState(0)
  const [branchId, setBranchId]     = useState('')
  const [allBranches, setAllBranches] = useState(true)
  const [activeFrom, setActiveFrom] = useState<string | null>(null)
  const [activeUntil, setActiveUntil] = useState<string | null>(null)
  const [status, setStatus]         = useState<'active' | 'inactive'>('active')
  const [branches, setBranches]     = useState<Branch[]>([])
  const [isLoading, setIsLoading]   = useState(false)
  const [isFetching, setIsFetching] = useState(isEdit)

  useEffect(() => { branchesApi.list().then(setBranches).catch(() => {}) }, [])

  useEffect(() => {
    if (!isEdit || !id) return
    packagesApi.get(id).then((p) => {
      setName(p.name); setHours(p.hours); setType(p.type); setPrice(p.price)
      setBranchId(p.branch_id ?? ''); setAllBranches(!p.branch_id)
      setActiveFrom(p.active_from); setActiveUntil(p.active_until); setStatus(p.status as 'active' | 'inactive')
    }).catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ')).finally(() => setIsFetching(false))
  }, [id, isEdit])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || price <= 0) { toast.error('กรุณากรอกชื่อและราคา'); return }
    setIsLoading(true)
    try {
      const payload = { name, hours, type, price, branch_id: allBranches ? undefined : branchId || undefined, active_from: activeFrom || undefined, active_until: activeUntil || undefined, status }
      if (isEdit && id) { await packagesApi.update(id, payload); toast.success('บันทึกสำเร็จ') }
      else              { await packagesApi.create(payload);     toast.success('เพิ่มแพ็กเกจสำเร็จ') }
      navigate('/packages')
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally { setIsLoading(false) }
  }

  if (isFetching) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
      <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/packages')}>← กลับ</Button>
      <h2 className="text-headline-sm font-display font-bold text-on-surface">{isEdit ? 'แก้ไขแพ็กเกจ' : 'เพิ่มแพ็กเกจใหม่'}</h2>
      <div className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <Input label="ชื่อแพ็กเกจ" value={name} onChange={(e) => setName(e.target.value)} required data-testid="package-form-name" />
        <div className="grid grid-cols-2 gap-4">
          <Input label="ชั่วโมง" type="number" min="1" value={String(hours)} onChange={(e) => setHours(Number(e.target.value))} required />
          <Input label="ราคา (฿)" type="number" min="0" value={String(price)} onChange={(e) => setPrice(Number(e.target.value))} required />
        </div>
        <Select label="ประเภท" options={[{ value: 'sale', label: 'ขายปกติ' }, { value: 'pre_sale', label: 'Pre-sale' }]} value={type} onChange={(e) => setType(e.target.value as PackageType)} />
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={allBranches} onChange={(e) => setAllBranches(e.target.checked)} className="form-checkbox rounded border-outline-variant text-secondary" />
          <span className="text-body-md text-on-surface">ใช้ได้ทุกสาขา</span>
        </label>
        {!allBranches && (
          <Select label="สาขา" options={branches.map((b) => ({ value: b.id, label: b.name }))} value={branchId} onChange={(e) => setBranchId(e.target.value)} />
        )}
        <div className="grid grid-cols-2 gap-4">
          <DatePicker label="ใช้งานตั้งแต่" value={activeFrom} onChange={setActiveFrom} max={activeUntil ?? undefined} />
          <DatePicker label="ใช้งานถึง"     value={activeUntil} onChange={setActiveUntil} min={activeFrom ?? undefined} />
        </div>
        <Select label="สถานะ" options={[{ value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }]} value={status} onChange={(e) => setStatus(e.target.value as 'active' | 'inactive')} />
      </div>
      <div className="flex gap-3">
        <Button type="submit" variant="primary" isLoading={isLoading} data-testid="package-form-submit">{isEdit ? 'บันทึก' : 'เพิ่มแพ็กเกจ'}</Button>
        <Button type="button" variant="ghost" onClick={() => navigate('/packages')}>ยกเลิก</Button>
      </div>
    </form>
  )
}
