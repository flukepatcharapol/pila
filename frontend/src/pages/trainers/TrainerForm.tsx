// =============================================================================
// pages/trainers/TrainerForm.tsx — Create / Edit trainer
// =============================================================================

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { trainersApi } from '@/api/trainers'
import { branchesApi } from '@/api/branches'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { ApiError } from '@/api/client'
import type { Branch } from '@/types'

export default function TrainerForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = Boolean(id)
  usePageTitle(isEdit ? 'แก้ไขเทรนเนอร์' : 'เพิ่มเทรนเนอร์')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { activeBranchId } = useAuth()

  const [name, setName]               = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail]             = useState('')
  const [branchId, setBranchId]       = useState(activeBranchId ?? '')
  const [status, setStatus]           = useState<'active' | 'inactive'>('active')
  const [branches, setBranches]       = useState<Branch[]>([])
  const [isLoading, setIsLoading]     = useState(false)
  const [isFetching, setIsFetching]   = useState(isEdit)

  useEffect(() => { branchesApi.list().then(setBranches).catch(() => {}) }, [])

  useEffect(() => {
    if (!isEdit || !id) return
    trainersApi.get(id).then((t) => {
      setName(t.name); setDisplayName(t.display_name); setEmail(t.email ?? ''); setBranchId(t.branch_id); setStatus(t.status)
    }).catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ')).finally(() => setIsFetching(false))
  }, [id, isEdit])

  // Auto-derive display_name from name while user types (can be overridden)
  function handleNameChange(v: string) {
    setName(v)
    if (!isEdit) setDisplayName(v)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !branchId) { toast.error('กรุณากรอกชื่อและเลือกสาขา'); return }
    setIsLoading(true)
    try {
      const payload = { name, display_name: displayName || name, email: email || undefined, branch_id: branchId, status }
      if (isEdit && id) { await trainersApi.update(id, payload); toast.success('บันทึกสำเร็จ') }
      else              { await trainersApi.create(payload);     toast.success('เพิ่มเทรนเนอร์สำเร็จ') }
      navigate('/trainers')
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally { setIsLoading(false) }
  }

  if (isFetching) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
      <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/trainers')}>← กลับ</Button>
      <h2 className="text-headline-sm font-display font-bold text-on-surface">{isEdit ? 'แก้ไขเทรนเนอร์' : 'เพิ่มเทรนเนอร์ใหม่'}</h2>
      <div className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <Input label="ชื่อ" value={name} onChange={(e) => handleNameChange(e.target.value)} required data-testid="trainer-form-name" />
        <Input label="ชื่อที่แสดง (ชื่อเล่น)" value={displayName} onChange={(e) => setDisplayName(e.target.value)} data-testid="trainer-form-display-name" />
        <Input label="อีเมล" type="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="trainer-form-email" />
        <Select label="สาขา" options={branches.map((b) => ({ value: b.id, label: b.name }))} value={branchId} onChange={(e) => setBranchId(e.target.value)} required data-testid="trainer-form-branch" />
        <Select label="สถานะ" options={[{ value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }]} value={status} onChange={(e) => setStatus(e.target.value as 'active' | 'inactive')} />
      </div>
      <div className="flex gap-3">
        <Button type="submit" variant="primary" isLoading={isLoading} data-testid="trainer-form-submit">{isEdit ? 'บันทึก' : 'เพิ่มเทรนเนอร์'}</Button>
        <Button type="button" variant="ghost" onClick={() => navigate('/trainers')}>ยกเลิก</Button>
      </div>
    </form>
  )
}
