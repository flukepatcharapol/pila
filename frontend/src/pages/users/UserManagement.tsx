// =============================================================================
// pages/users/UserManagement.tsx — User list with slide-out detail panel
// =============================================================================

import { useState } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useTable } from '@/hooks/useTable'
import { usersApi } from '@/api/users'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { UserDetailPanel } from '@/components/users/UserDetailPanel'
import type { User, Role } from '@/types'

const ROLE_LABELS: Record<Role, string> = {
  developer: 'Developer', owner: 'Owner', branch_master: 'Branch Master', admin: 'Admin', trainer: 'Trainer',
}
const ROLE_COLORS: Record<Role, string> = {
  developer:    'bg-purple-100 text-purple-700 border-purple-200',
  owner:        'bg-primary/10 text-primary border-primary/20',
  branch_master:'bg-secondary/10 text-secondary border-secondary/20',
  admin:        'bg-tertiary/10 text-tertiary border-tertiary/20',
  trainer:      'bg-surface-container-high text-on-surface-variant border-outline-variant',
}

export default function UserManagement() {
  usePageTitle('ผู้ใช้งาน')
  const { data, total, isLoading, params, setSearch, setPage, setStatus, refresh } = useTable(usersApi.list)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  const columns: TableColumn<User>[] = [
    {
      key: 'display_name', label: 'ชื่อ', sortable: true,
      render: (r) => (
        <button type="button" className="text-left hover:underline font-medium text-on-surface" onClick={() => setSelectedUser(r)} data-testid={`user-row-${r.id}`}>
          {r.display_name}
        </button>
      ),
    },
    { key: 'email', label: 'อีเมล', render: (r) => <span className="text-body-sm text-on-surface-variant">{r.email}</span> },
    {
      key: 'role', label: 'บทบาท',
      render: (r) => (
        <span className={`inline-flex px-2 py-0.5 rounded-full text-label-sm font-medium border ${ROLE_COLORS[r.role]}`}>
          {ROLE_LABELS[r.role]}
        </span>
      ),
    },
    { key: 'status', label: 'สถานะ', render: (r) => <StatusBadge label={r.status === 'active' ? 'ใช้งาน' : 'ระงับ'} variant={resolveStatusVariant(r.status)} /> },
    {
      key: 'actions', label: '',
      render: (r) => <Button variant="ghost" size="sm" onClick={() => setSelectedUser(r)}>รายละเอียด</Button>,
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <div className="w-64"><Input placeholder="ค้นหาชื่อ, อีเมล…" value={params.search ?? ''} onChange={(e) => setSearch(e.target.value)} data-testid="user-list-search" /></div>
          <div className="w-44">
            <Select options={[
              { value: '', label: 'ทุกบทบาท' },
              ...(['developer','owner','branch_master','admin','trainer'] as Role[]).map((r) => ({ value: r, label: ROLE_LABELS[r] }))
            ]} value={params.role ?? ''} onChange={(e) => { /* role filter via setExtraParams */ }} />
          </div>
          <div className="w-36">
            <Select options={[{ value: '', label: 'ทุกสถานะ' }, { value: 'active', label: 'ใช้งาน' }, { value: 'inactive', label: 'ระงับ' }]}
              value={params.status ?? ''} onChange={(e) => setStatus(e.target.value || null)} />
          </div>
        </div>
      </div>

      <Table columns={columns} data={data} isLoading={isLoading} emptyMessage="ไม่พบผู้ใช้งาน" rowKey={(r) => r.id} />
      <Pagination total={total} page={params.page ?? 1} pageSize={params.page_size ?? 20} onChange={setPage} />

      <UserDetailPanel user={selectedUser} onClose={() => setSelectedUser(null)} onUpdated={refresh} />
    </div>
  )
}
