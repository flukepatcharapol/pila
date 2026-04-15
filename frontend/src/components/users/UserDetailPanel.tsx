// =============================================================================
// components/users/UserDetailPanel.tsx — Slide-out drawer for user detail
// =============================================================================

import { useState } from 'react'
import { useToast } from '@/hooks/useToast'
import { usersApi } from '@/api/users'
import { useAuth } from '@/stores/AuthContext'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import type { User, Role } from '@/types'

const ROLE_LABELS: Record<Role, string> = {
  developer: 'Developer', owner: 'Owner', branch_master: 'Branch Master', admin: 'Admin', trainer: 'Trainer',
}

const ROLE_ORDER: Role[] = ['developer', 'owner', 'branch_master', 'admin', 'trainer']

interface UserDetailPanelProps {
  user: User | null
  onClose: () => void
  onUpdated: () => void
}

export function UserDetailPanel({ user, onClose, onUpdated }: UserDetailPanelProps) {
  const { toast } = useToast()
  const { user: currentUser } = useAuth()
  const [newRole, setNewRole]       = useState<Role | ''>(user?.role ?? '')
  const [isSavingRole, setIsSavingRole] = useState(false)
  const [isDeactivating, setIsDeactivating] = useState(false)

  if (!user) return null

  // Roles the current user can assign — only roles strictly below their own
  const currentRoleIdx = currentUser ? ROLE_ORDER.indexOf(currentUser.role) : -1
  const assignableRoles: Role[] = ROLE_ORDER.filter((_, i) => i > currentRoleIdx)

  async function handleRoleChange() {
    if (!newRole || newRole === user.role) return
    setIsSavingRole(true)
    try {
      await usersApi.setRole(user.id, newRole as Role)
      toast.success('เปลี่ยนบทบาทสำเร็จ')
      onUpdated()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'เปลี่ยนบทบาทไม่สำเร็จ')
    } finally { setIsSavingRole(false) }
  }

  async function handleDeactivate() {
    setIsDeactivating(true)
    try {
      await usersApi.delete(user.id)
      toast.success('ระงับผู้ใช้งานสำเร็จ')
      onUpdated(); onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ระงับไม่สำเร็จ')
    } finally { setIsDeactivating(false) }
  }

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-overlay bg-inverse-surface/30 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      {/* Panel */}
      <aside className="fixed right-0 top-0 h-screen w-80 z-modal bg-surface-container-lowest shadow-elevated flex flex-col animate-slide-in-right" aria-label="รายละเอียดผู้ใช้">
        <div className="flex items-center justify-between px-5 py-4 border-b border-outline-variant">
          <h3 className="text-title-md font-semibold text-on-surface">รายละเอียดผู้ใช้</h3>
          <button type="button" onClick={onClose} className="p-1 rounded-md text-on-surface-variant hover:bg-surface-container-low transition-colors" aria-label="ปิด">
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Profile */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center shrink-0">
              <span className="text-on-secondary font-bold text-title-sm">{user.display_name.charAt(0).toUpperCase()}</span>
            </div>
            <div>
              <p className="text-body-md font-semibold text-on-surface">{user.display_name}</p>
              <p className="text-body-sm text-on-surface-variant">{user.email}</p>
            </div>
          </div>

          <div className="space-y-3 text-body-sm">
            {[
              { label: 'Username', value: user.username },
              { label: 'บทบาท',   value: ROLE_LABELS[user.role] },
              { label: 'สถานะ',   value: <StatusBadge label={user.status === 'active' ? 'ใช้งาน' : 'ระงับ'} variant={resolveStatusVariant(user.status)} /> },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between items-center">
                <span className="text-on-surface-variant">{label}</span>
                <span className="font-medium text-on-surface">{value}</span>
              </div>
            ))}
          </div>

          {/* Role change */}
          {assignableRoles.length > 0 && user.status === 'active' && (
            <div className="pt-4 border-t border-outline-variant space-y-3">
              <p className="text-label-md font-semibold text-on-surface">เปลี่ยนบทบาท</p>
              <Select
                options={assignableRoles.map((r) => ({ value: r, label: ROLE_LABELS[r] }))}
                value={newRole}
                onChange={(e) => setNewRole(e.target.value as Role)}
                data-testid="user-panel-role-select"
              />
              <Button variant="secondary" size="sm" onClick={handleRoleChange} isLoading={isSavingRole} disabled={!newRole || newRole === user.role} data-testid="user-panel-save-role-btn">
                บันทึกบทบาท
              </Button>
            </div>
          )}
        </div>

        {/* Footer actions */}
        {user.id !== currentUser?.id && user.status === 'active' && (
          <div className="p-5 border-t border-outline-variant">
            <Button variant="danger" className="w-full" onClick={handleDeactivate} isLoading={isDeactivating} data-testid="user-panel-deactivate-btn">
              ระงับผู้ใช้งาน
            </Button>
          </div>
        )}
      </aside>
    </>
  )
}

export default UserDetailPanel
