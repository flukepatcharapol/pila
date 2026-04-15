// =============================================================================
// pages/settings/BranchConfig.tsx — Branch configuration management
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { branchesApi } from '@/api/branches'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { ApiError } from '@/api/client'
import type { BranchDetail, SourceType } from '@/types'

export default function BranchConfig() {
  usePageTitle('จัดการสาขา')
  const { toast } = useToast()

  const [branches, setBranches]   = useState<BranchDetail[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [editing, setEditing]     = useState<BranchDetail | null>(null)
  const [isSaving, setIsSaving]   = useState(false)

  // Edit form state
  const [openingHour, setOpeningHour]   = useState('')
  const [closingHour, setClosingHour]   = useState('')
  const [sourceTypes, setSourceTypes]   = useState<SourceType[]>([])
  const [newSourceLabel, setNewSourceLabel] = useState('')
  const [newSourceCode, setNewSourceCode]   = useState('')

  async function loadBranches() {
    setIsLoading(true)
    try {
      const list = await branchesApi.list()
      // Load details for each branch (includes source types)
      const details = await Promise.all(list.map((b) => branchesApi.get(b.id)))
      setBranches(details)
    } catch { toast.error('โหลดข้อมูลไม่สำเร็จ') }
    finally { setIsLoading(false) }
  }

  useEffect(() => { loadBranches() }, [])

  function openEdit(branch: BranchDetail) {
    setEditing(branch)
    setOpeningHour(branch.opening_hour ?? '')
    setClosingHour(branch.closing_hour ?? '')
    setSourceTypes([...branch.source_types])
  }

  function addSourceType() {
    if (!newSourceLabel || !newSourceCode) return
    setSourceTypes((prev) => [...prev, { id: `new-${Date.now()}`, label: newSourceLabel, code: newSourceCode, branch_id: editing?.id ?? '' }])
    setNewSourceLabel(''); setNewSourceCode('')
  }

  async function handleSave() {
    if (!editing) return
    setIsSaving(true)
    try {
      await branchesApi.update(editing.id, { opening_hour: openingHour || null, closing_hour: closingHour || null } as Partial<BranchDetail>)
      toast.success('บันทึกสำเร็จ')
      setEditing(null)
      loadBranches()
    } catch (err) {
      toast.error(err instanceof ApiError ? (err.detail ?? 'บันทึกไม่สำเร็จ') : 'บันทึกไม่สำเร็จ')
    } finally { setIsSaving(false) }
  }

  return (
    <div className="space-y-4 max-w-3xl">
      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-20 rounded-xl bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer" />)}</div>
      ) : (
        <div className="space-y-3">
          {branches.map((branch) => (
            <div key={branch.id} className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-title-sm font-semibold text-on-surface">{branch.name}</p>
                  <p className="text-body-sm text-on-surface-variant mt-0.5">
                    เปิด: {branch.opening_hour ?? '—'} – {branch.closing_hour ?? '—'}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {branch.source_types.map((s) => (
                      <span key={s.id} className="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary text-label-sm">{s.label} ({s.code})</span>
                    ))}
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => openEdit(branch)} data-testid={`branch-edit-${branch.id}`}>แก้ไข</Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={!!editing} onClose={() => setEditing(null)} title={`แก้ไข: ${editing?.name}`} size="md"
        footer={<><Button variant="ghost" onClick={() => setEditing(null)}>ยกเลิก</Button><Button variant="primary" onClick={handleSave} isLoading={isSaving}>บันทึก</Button></>}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="เปิดทำการ (HH:MM)" type="time" value={openingHour} onChange={(e) => setOpeningHour(e.target.value)} />
            <Input label="ปิดทำการ (HH:MM)"  type="time" value={closingHour}  onChange={(e) => setClosingHour(e.target.value)} />
          </div>
          <div>
            <p className="text-label-md font-semibold text-on-surface mb-2">แหล่งที่มา (Source Types)</p>
            <div className="space-y-2 mb-3">
              {sourceTypes.map((s, i) => (
                <div key={s.id} className="flex items-center gap-2">
                  <span className="flex-1 text-body-md">{s.label} <span className="text-secondary font-mono">({s.code})</span></span>
                  <button type="button" className="text-error text-label-sm hover:underline" onClick={() => setSourceTypes((prev) => prev.filter((_, j) => j !== i))}>ลบ</button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Input placeholder="ชื่อ" value={newSourceLabel} onChange={(e) => setNewSourceLabel(e.target.value)} />
              <Input placeholder="รหัส" value={newSourceCode}  onChange={(e) => setNewSourceCode(e.target.value)} />
              <Button type="button" variant="ghost" size="sm" onClick={addSourceType}>+</Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
