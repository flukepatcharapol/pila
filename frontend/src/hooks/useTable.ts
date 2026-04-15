// =============================================================================
// hooks/useTable.ts — Centralised state for paginated server-side tables
// All list pages (customers, orders, sessions, etc.) share the same pattern:
//   search → debounce → fetch → display → paginate → sort
// This hook encapsulates that pattern so pages don't repeat it.
// =============================================================================

import { useState, useEffect, useCallback, useRef } from 'react'
import type { PaginatedResponse, ListParams } from '@/types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TableState<T> {
  data: T[]
  total: number
  isLoading: boolean
  error: string | null
  params: ListParams
  // Setters exposed to the consuming component
  setSearch: (search: string) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  setSort: (sortBy: string, sortDir: 'asc' | 'desc') => void
  setBranchId: (branchId: string | null) => void
  setStatus: (status: string | null) => void
  setExtraParams: (extra: Partial<ListParams>) => void
  refresh: () => void
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

// Generic fetcher type — matches all API list functions
type ListFetcher<T> = (params: ListParams) => Promise<PaginatedResponse<T>>

export function useTable<T>(
  fetcher: ListFetcher<T>,
  initialParams: ListParams = {},
): TableState<T> {
  // Current list of records shown in the table
  const [data, setData] = useState<T[]>([])
  // Total count from the server (used by Pagination component)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Merge initial params with sensible defaults
  const [params, setParams] = useState<ListParams>({
    page: 1,
    page_size: 20,
    ...initialParams,
  })

  // Pending search value — we debounce before writing it to params
  const [rawSearch, setRawSearch] = useState(initialParams.search ?? '')
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Track a fetch counter so stale responses from cancelled fetches are ignored
  const fetchCounter = useRef(0)

  // ---------------------------------------------------------------------------
  // Fetch function — called whenever params change
  // ---------------------------------------------------------------------------

  const fetchData = useCallback(async () => {
    // Increment counter before fetch; capture current value for comparison after
    const thisCall = ++fetchCounter.current
    setIsLoading(true)
    setError(null)

    try {
      const result = await fetcher(params)
      // Only update state if this is still the most recent fetch
      if (thisCall === fetchCounter.current) {
        setData(result.items)
        setTotal(result.total)
      }
    } catch (err) {
      if (thisCall === fetchCounter.current) {
        setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาด')
        setData([])
        setTotal(0)
      }
    } finally {
      if (thisCall === fetchCounter.current) {
        setIsLoading(false)
      }
    }
  }, [fetcher, params])

  // Re-fetch whenever params change (page, sort, branch filter, etc.)
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // ---------------------------------------------------------------------------
  // Setters
  // ---------------------------------------------------------------------------

  // Debounced search: wait 300ms after the last keystroke before fetching
  const setSearch = useCallback((search: string) => {
    setRawSearch(search)
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      // Reset to page 1 when searching so the user sees results from the start
      setParams((prev) => ({ ...prev, search: search || undefined, page: 1 }))
    }, 300)
  }, [])

  // Page change — keep other params intact
  const setPage = useCallback((page: number) => {
    setParams((prev) => ({ ...prev, page }))
  }, [])

  const setPageSize = useCallback((page_size: number) => {
    setParams((prev) => ({ ...prev, page_size, page: 1 }))
  }, [])

  // Sort column + direction toggle
  const setSort = useCallback((sort_by: string, sort_dir: 'asc' | 'desc') => {
    setParams((prev) => ({ ...prev, sort_by, sort_dir, page: 1 }))
  }, [])

  // Branch chip filter — null clears the filter
  const setBranchId = useCallback((branch_id: string | null) => {
    setParams((prev) => ({
      ...prev,
      branch_id: branch_id ?? undefined,
      page: 1,
    }))
  }, [])

  // Status dropdown filter — null clears the filter
  const setStatus = useCallback((status: string | null) => {
    setParams((prev) => ({
      ...prev,
      status: status ?? undefined,
      page: 1,
    }))
  }, [])

  // Escape hatch: set arbitrary extra params (e.g. customer_id, start_date)
  const setExtraParams = useCallback((extra: Partial<ListParams>) => {
    setParams((prev) => ({ ...prev, ...extra, page: 1 }))
  }, [])

  // Manual refresh — keeps current params, just re-fetches
  const refresh = useCallback(() => {
    fetchData()
  }, [fetchData])

  // Expose rawSearch so the Input component can show what the user typed
  // (params.search is debounced and lags behind)
  void rawSearch // referenced to avoid lint warning; Input reads params.search directly

  return {
    data,
    total,
    isLoading,
    error,
    params,
    setSearch,
    setPage,
    setPageSize,
    setSort,
    setBranchId,
    setStatus,
    setExtraParams,
    refresh,
  }
}
