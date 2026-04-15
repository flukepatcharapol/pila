// =============================================================================
// pages/customers/CustomerList.tsx — Paginated customer list with CRUD actions
// Uses useTable() for unified search/sort/pagination state management.
// =============================================================================

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useTable } from '@/hooks/useTable'
import { useAuth } from '@/stores/AuthContext'
import { customersApi } from '@/api/customers'
import { Table, type TableColumn } from '@/components/ui/Table'
import { Pagination } from '@/components/ui/Pagination'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { StatusBadge, resolveStatusVariant } from '@/components/ui/StatusBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import type { Customer } from '@/types'

export default function CustomerList() {
  usePageTitle('ลูกค้า')
  const navigate = useNavigate()
  const { toast } = useToast()
  const { user } = useAuth()

  // useTable handles pagination, search debounce, sort, and fetching
  const {
    data: customers,
    total,
    isLoading,
    params,
    setSearch,
    setPage,
    setSort,
    setStatus,
    refresh,
  } = useTable(customersApi.list)

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
  const [isDeleting, setIsDeleting]     = useState(false)

  // Only admin+ can delete; trainers can only view
  const canDelete = user?.role !== 'trainer'
  const canCreate = user?.role !== 'trainer'

  // ---------------------------------------------------------------------------
  // Table columns definition
  // ---------------------------------------------------------------------------

  const columns: TableColumn<Customer>[] = [
    {
      key: 'code',
      label: 'รหัส',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-label-md text-secondary">{row.code}</span>
      ),
    },
    {
      key: 'display_name',
      label: 'ชื่อ',
      sortable: true,
      render: (row) => (
        <div>
          <p className="text-body-md text-on-surface font-medium">{row.display_name}</p>
          {row.nickname && (
            <p className="text-body-sm text-on-surface-variant">({row.nickname})</p>
          )}
        </div>
      ),
    },
    {
      key: 'phone',
      label: 'เบอร์โทร',
      render: (row) => (
        <span className="text-body-md text-on-surface">{row.phone ?? '—'}</span>
      ),
    },
    {
      key: 'remaining_hours',
      label: 'เซสชันคงเหลือ',
      sortable: true,
      render: (row) => (
        <span
          className={[
            'font-semibold text-body-md tabular-nums',
            row.remaining_hours <= 0 ? 'text-error' : 'text-tertiary',
          ].join(' ')}
        >
          {row.remaining_hours} ชม.
        </span>
      ),
    },
    {
      key: 'status',
      label: 'สถานะ',
      render: (row) => (
        <StatusBadge
          label={row.status === 'active' ? 'ใช้งาน' : 'ระงับ'}
          variant={resolveStatusVariant(row.status)}
        />
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (row) => (
        <div className="flex items-center gap-2 justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/customers/${row.id}`)}
            data-testid={`customer-list-view-btn-${row.id}`}
          >
            ดู
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/customers/${row.id}/edit`)}
            data-testid={`customer-list-edit-btn-${row.id}`}
          >
            แก้ไข
          </Button>
          {canDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setDeleteTarget(row)}
              data-testid={`customer-list-delete-btn-${row.id}`}
            >
              ลบ
            </Button>
          )}
        </div>
      ),
    },
  ]

  // ---------------------------------------------------------------------------
  // Delete handler
  // ---------------------------------------------------------------------------

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    try {
      await customersApi.delete(deleteTarget.id)
      toast.success(`ลบลูกค้า "${deleteTarget.display_name}" สำเร็จ`)
      setDeleteTarget(null)
      refresh()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'ลบไม่สำเร็จ')
    } finally {
      setIsDeleting(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* ── Toolbar ── */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-3 flex-1">
          {/* Search input */}
          <div className="w-full md:w-72">
            <Input
              placeholder="ค้นหาชื่อ, รหัส, เบอร์โทร…"
              value={params.search ?? ''}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="customer-list-search"
            />
          </div>

          {/* Status filter */}
          <div className="w-40">
            <Select
              options={[
                { value: '', label: 'ทุกสถานะ' },
                { value: 'active', label: 'ใช้งาน' },
                { value: 'inactive', label: 'ระงับ' },
              ]}
              value={params.status ?? ''}
              onChange={(e) => setStatus(e.target.value || null)}
              data-testid="customer-list-status-filter"
            />
          </div>
        </div>

        {/* Add button — hidden for trainer role */}
        {canCreate && (
          <Button
            variant="primary"
            onClick={() => navigate('/customers/new')}
            data-testid="customer-list-add-btn"
          >
            + เพิ่มลูกค้า
          </Button>
        )}
      </div>

      {/* ── Table ── */}
      <Table
        columns={columns}
        data={customers}
        isLoading={isLoading}
        emptyMessage="ไม่พบลูกค้า — ลองเปลี่ยนคำค้นหาหรือเพิ่มลูกค้าใหม่"
        sortBy={params.sort_by}
        sortDir={params.sort_dir}
        onSort={(key) =>
          setSort(key, params.sort_by === key && params.sort_dir === 'asc' ? 'desc' : 'asc')
        }
        rowKey={(row) => row.id}
      />

      {/* ── Pagination ── */}
      <Pagination
        total={total}
        page={params.page ?? 1}
        pageSize={params.page_size ?? 20}
        onChange={setPage}
      />

      {/* ── Delete confirmation dialog (CR-10) ── */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        title="ลบลูกค้า"
        description={`ต้องการลบ "${deleteTarget?.display_name}" ออกจากระบบใช่ไหม? การกระทำนี้ไม่สามารถยกเลิกได้`}
        confirmLabel="ลบ"
        isDanger
        isLoading={isDeleting}
      />
    </div>
  )
}
