// =============================================================================
// pages/permissions/PermissionMatrix.tsx — Role × module × action permission grid
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { permissionsApi } from '@/api/permissions'
import type { PermissionCell, FeatureToggle, Role } from '@/types'

const ROLES: Role[] = ['branch_master', 'admin', 'trainer']
const ROLE_LABELS: Record<string, string> = { branch_master: 'Branch Master', admin: 'Admin', trainer: 'Trainer' }
const ACTIONS = ['view', 'create', 'edit', 'delete'] as const

export default function PermissionMatrix() {
  usePageTitle('สิทธิ์การเข้าถึง')
  const { toast } = useToast()

  const [cells, setCells]               = useState<PermissionCell[]>([])
  const [toggles, setToggles]           = useState<FeatureToggle[]>([])
  const [isLoading, setIsLoading]       = useState(true)
  const [saving, setSaving]             = useState<string | null>(null)

  useEffect(() => {
    Promise.all([permissionsApi.getMatrix(), permissionsApi.getFeatureToggles()])
      .then(([c, t]) => { setCells(c); setToggles(t) })
      .catch(() => toast.error('โหลดข้อมูลไม่สำเร็จ'))
      .finally(() => setIsLoading(false))
  }, [])

  function getCell(role: Role, module: string, action: string): boolean {
    return cells.find((c) => c.role === role && c.module === module && c.action === action as never)?.allowed ?? false
  }

  async function toggleCell(role: Role, module: string, action: string, current: boolean) {
    const key = `${role}-${module}-${action}`
    setSaving(key)
    const updated: PermissionCell = { role, module, action: action as PermissionCell['action'], allowed: !current }
    try {
      await permissionsApi.update([updated])
      setCells((prev) => {
        const idx = prev.findIndex((c) => c.role === role && c.module === module && c.action === action)
        if (idx >= 0) { const next = [...prev]; next[idx] = updated; return next }
        return [...prev, updated]
      })
    } catch { toast.error('บันทึกไม่สำเร็จ') }
    finally { setSaving(null) }
  }

  async function handleFeatureToggle(module: string, current: boolean) {
    try {
      await permissionsApi.updateFeatureToggle(module, !current)
      setToggles((prev) => prev.map((t) => t.module === module ? { ...t, enabled: !current } : t))
      toast.success('บันทึกสำเร็จ')
    } catch { toast.error('บันทึกไม่สำเร็จ') }
  }

  // Get unique modules from cells
  const modules = [...new Set(cells.map((c) => c.module))]

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="space-y-8">
      {/* Feature Toggles */}
      <section>
        <h3 className="text-title-md font-display font-semibold text-on-surface mb-3">Feature Toggles</h3>
        <div className="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden">
          {toggles.map((t, i) => (
            <div key={t.module} className={`flex items-center justify-between px-4 py-3 ${i > 0 ? 'border-t border-outline-variant' : ''}`}>
              <span className="text-body-md text-on-surface">{t.label}</span>
              <button type="button" onClick={() => handleFeatureToggle(t.module, t.enabled)}
                className={`relative w-10 h-6 rounded-full transition-colors ${t.enabled ? 'bg-tertiary' : 'bg-surface-container-high'}`}
                data-testid={`feature-toggle-${t.module}`}>
                <span className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${t.enabled ? 'translate-x-5' : 'translate-x-1'}`} />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Permission Matrix */}
      <section>
        <h3 className="text-title-md font-display font-semibold text-on-surface mb-3">Permission Matrix</h3>
        <div className="overflow-x-auto rounded-xl border border-outline-variant">
          <table className="w-full text-left border-collapse">
            <thead className="bg-surface-container-low">
              <tr>
                <th className="px-4 py-3 text-label-md font-semibold text-on-surface-variant w-40">โมดูล</th>
                <th className="px-4 py-3 text-label-md font-semibold text-on-surface-variant w-28">Action</th>
                {ROLES.map((r) => (
                  <th key={r} className="px-4 py-3 text-label-md font-semibold text-on-surface-variant text-center">{ROLE_LABELS[r]}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant">
              {modules.flatMap((mod) =>
                ACTIONS.map((action, aIdx) => (
                  <tr key={`${mod}-${action}`} className={aIdx === 0 ? 'border-t-2 border-outline' : ''}>
                    <td className="px-4 py-2 text-body-sm text-on-surface font-medium">{aIdx === 0 ? mod : ''}</td>
                    <td className="px-4 py-2 text-body-sm text-on-surface-variant capitalize">{action}</td>
                    {ROLES.map((role) => {
                      const allowed = getCell(role, mod, action)
                      const key = `${role}-${mod}-${action}`
                      return (
                        <td key={role} className="px-4 py-2 text-center">
                          <button type="button" onClick={() => toggleCell(role, mod, action, allowed)}
                            disabled={saving === key}
                            className={`w-5 h-5 rounded border-2 transition-colors ${allowed ? 'bg-tertiary border-tertiary' : 'bg-surface-container-lowest border-outline-variant hover:border-secondary'}`}
                            data-testid={`perm-${role}-${mod}-${action}`}
                          >
                            {allowed && <svg className="w-3 h-3 text-on-tertiary mx-auto" fill="currentColor" viewBox="0 0 12 12"><path fillRule="evenodd" d="M10.28 2.28L4 8.56 1.72 6.28A1 1 0 00.28 7.72l3 3a1 1 0 001.44 0l7-7a1 1 0 00-1.44-1.44z" clipRule="evenodd" /></svg>}
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
