// =============================================================================
// pages/caretakers/CaretakerForm.tsx — Create / Edit caretaker
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { caretakersApi } from '@/api/caretakers'
import { branchesApi } from '@/api/branches'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { ApiError } from '@/api/client'
import type { Branch } from '@/types'

export default function CaretakerForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  usePageTitle(isEdit ? 'แก้ไขผู้ดูแลเด็ก' : 'เพิ่มผู้ดูแลเด็ก')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { activeBranchId } = useAuth()

  const [name, setName]           = useState('')
  const [email, setEmail]         = useState('')
  const [branchId, setBranchId]   = useState(activeBranchId ?? '')
  const [status, setStatus]       = useState<'active' | 'inactive'>('active')
  const [branches, setBranches]   = useState<Branch[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(isEdit)

  useEffect(() => { branchesApi.list().then(setBranches).catch(() => {}) }, [])

  useEffect(() => {
    if (!isEdit || !id) return
    caretakersApi.get(id).then((c) => {
      setName(c.name); setEmail(c.email ?? ''); setBranchId(c.branch_id); setStatus(c.status)
    }).catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ')).finally(() => setIsFetching(false))
  }, [id, isEdit])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !branchId) { toast.error('กรุณากรอกชื่อและเลือกสาขา'); return }
    setIsLoading(true)
    try {
      const payload = { name, email: email || undefined, branch_id: branchId, status }
      if (isEdit && id) { await caretakersApi.update(id, payload); toast.success('บันทึกสำเร็จ') }
      else              { await caretakersApi.create(payload);     toast.success('เพิ่มผู้ดูแลเด็กสำเร็จ') }
      navigate('/caretakers')
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally { setIsLoading(false) }
  }

  if (isFetching) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
      <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/caretakers')}>← กลับ</Button>
      <h2 className="text-headline-sm font-display font-bold text-on-surface">{isEdit ? 'แก้ไขผู้ดูแลเด็ก' : 'เพิ่มผู้ดูแลเด็กใหม่'}</h2>
      <div className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <Input label="ชื่อ" value={name} onChange={(e) => setName(e.target.value)} required data-testid="caretaker-form-name" />
        <Input label="อีเมล" type="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="caretaker-form-email" />
        <Select label="สาขา" options={branches.map((b) => ({ value: b.id, label: b.name }))} value={branchId} onChange={(e) => setBranchId(e.target.value)} required />
        <Select label="สถานะ" options={[{ value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }]} value={status} onChange={(e) => setStatus(e.target.value as 'active' | 'inactive')} />
      </div>
      <div className="flex gap-3">
        <Button type="submit" variant="primary" isLoading={isLoading} data-testid="caretaker-form-submit">{isEdit ? 'บันทึก' : 'เพิ่มผู้ดูแลเด็ก'}</Button>
        <Button type="button" variant="ghost" onClick={() => navigate('/caretakers')}>ยกเลิก</Button>
      </div>
    </form>
  )
}
