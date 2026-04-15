// =============================================================================
// components/ui/Table.tsx — Reusable paginated data table
// Used by every list page. Supports server-side sort (via onSort callback),
// loading shimmer skeleton, and a customisable empty state message.
// =============================================================================

import type { ReactNode } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TableColumn<T> {
  key: string
  label: string
  sortable?: boolean
  // Custom renderer — if omitted, the raw cell value is rendered as a string
  render?: (row: T) => ReactNode
}

interface TableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  isLoading?: boolean
  emptyMessage?: string
  // Controlled sort state — set by the parent via useTable()
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  onSort?: (key: string) => void
  // Optional row key function; defaults to index
  rowKey?: (row: T, index: number) => string
}

// ---------------------------------------------------------------------------
// Shimmer skeleton row — shown when loading
// ---------------------------------------------------------------------------

function ShimmerRow({ columns }: { columns: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          {/* Animated shimmer bar at 60–80% width to mimic varying content */}
          <div
            className="h-4 rounded bg-gradient-to-r from-surface-container-high via-surface-container-lowest to-surface-container-high bg-[length:200%_100%] animate-shimmer"
            style={{ width: `${60 + (i % 3) * 10}%` }}
          />
        </td>
      ))}
    </tr>
  )
}

// ---------------------------------------------------------------------------
// Sort indicator — ▲ / ▼ arrow shown in the active column header
// ---------------------------------------------------------------------------

function SortIndicator({ active, dir }: { active: boolean; dir?: 'asc' | 'desc' }) {
  if (!active) {
    // Inactive column: show a neutral double-arrow hint
    return (
      <span className="ml-1 text-on-surface-variant opacity-40 text-xs">⇅</span>
    )
  }
  return (
    <span className="ml-1 text-secondary text-xs">
      {dir === 'asc' ? '▲' : '▼'}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Main component — generic over row type T
// ---------------------------------------------------------------------------

export function Table<T>({
  columns,
  data,
  isLoading = false,
  emptyMessage = 'ไม่มีข้อมูล',
  sortBy,
  sortDir,
  onSort,
  rowKey,
}: TableProps<T>) {
  // Handle column header click: toggle direction if same column, else sort asc
  function handleSort(key: string) {
    if (!onSort) return
    if (sortBy === key) {
      // Same column clicked — flip direction
      onSort(key)
    } else {
      // New column — always start ascending
      onSort(key)
    }
  }

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-outline-variant">
      <table className="w-full text-left border-collapse">
        {/* ── Header ── */}
        <thead className="bg-surface-container-low">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={[
                  'px-4 py-3 text-label-md font-semibold text-on-surface-variant',
                  'whitespace-nowrap select-none',
                  col.sortable && onSort ? 'cursor-pointer hover:text-on-surface' : '',
                ].join(' ')}
                onClick={() => col.sortable && handleSort(col.key)}
              >
                {col.label}
                {col.sortable && (
                  <SortIndicator active={sortBy === col.key} dir={sortDir} />
                )}
              </th>
            ))}
          </tr>
        </thead>

        {/* ── Body ── */}
        <tbody className="divide-y divide-outline-variant">
          {isLoading
            ? // Show 5 shimmer skeleton rows while data is loading
              Array.from({ length: 5 }).map((_, i) => (
                <ShimmerRow key={i} columns={columns.length} />
              ))
            : data.length === 0
            ? // Empty state — single cell spanning all columns
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-16 text-center text-on-surface-variant text-body-md leading-thai"
                >
                  {emptyMessage}
                </td>
              </tr>
            : // Normal data rows
              data.map((row, index) => (
                <tr
                  key={rowKey ? rowKey(row, index) : index}
                  className="hover:bg-surface-container-low transition-colors duration-100"
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-body-md text-on-surface">
                      {col.render
                        ? col.render(row)
                        : String((row as Record<string, unknown>)[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  )
}

export default Table
