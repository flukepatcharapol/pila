// =============================================================================
// components/ui/Pagination.tsx — Page navigation controls for list pages
// Shows "แสดง X–Y จาก Z รายการ" + Previous/Next + page number pills.
// Hides entirely when total fits on one page (total <= pageSize).
// =============================================================================

interface PaginationProps {
  total: number
  page: number
  pageSize: number
  onChange: (page: number) => void
}

export function Pagination({ total, page, pageSize, onChange }: PaginationProps) {
  // No pagination needed when everything fits on one page
  if (total <= pageSize) return null

  const totalPages = Math.ceil(total / pageSize)
  // First and last visible item index (1-based for the label)
  const firstItem = (page - 1) * pageSize + 1
  const lastItem = Math.min(page * pageSize, total)

  // Generate page numbers to show: always show first, last, current ±1, and ellipsis
  function getPageNumbers(): (number | 'ellipsis')[] {
    const delta = 1  // pages to show on each side of current
    const pages: (number | 'ellipsis')[] = []

    let prev = -1
    for (let p = 1; p <= totalPages; p++) {
      // Show: first page, last page, current ± delta
      if (
        p === 1 ||
        p === totalPages ||
        (p >= page - delta && p <= page + delta)
      ) {
        if (prev !== -1 && p - prev > 1) {
          pages.push('ellipsis')
        }
        pages.push(p)
        prev = p
      }
    }
    return pages
  }

  const pageNumbers = getPageNumbers()

  return (
    <div className="flex items-center justify-between mt-4 flex-wrap gap-3">
      {/* Record count label */}
      <p className="text-body-sm text-on-surface-variant">
        แสดง {firstItem.toLocaleString()}–{lastItem.toLocaleString()} จาก{' '}
        {total.toLocaleString()} รายการ
      </p>

      {/* Page navigation */}
      <div className="flex items-center gap-1">
        {/* Previous button */}
        <button
          type="button"
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="px-3 py-1.5 rounded-md text-label-md text-on-surface-variant border border-outline-variant hover:bg-surface-container-low disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="หน้าก่อน"
        >
          ‹
        </button>

        {/* Page number pills */}
        {pageNumbers.map((p, i) =>
          p === 'ellipsis' ? (
            <span key={`ell-${i}`} className="px-2 text-on-surface-variant">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              onClick={() => onChange(p)}
              aria-current={p === page ? 'page' : undefined}
              className={[
                'w-9 h-9 rounded-md text-label-md font-medium transition-colors',
                p === page
                  ? 'bg-secondary text-on-secondary'
                  : 'text-on-surface-variant border border-outline-variant hover:bg-surface-container-low',
              ].join(' ')}
            >
              {p}
            </button>
          ),
        )}

        {/* Next button */}
        <button
          type="button"
          onClick={() => onChange(page + 1)}
          disabled={page === totalPages}
          className="px-3 py-1.5 rounded-md text-label-md text-on-surface-variant border border-outline-variant hover:bg-surface-container-low disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="หน้าถัดไป"
        >
          ›
        </button>
      </div>
    </div>
  )
}

export default Pagination
