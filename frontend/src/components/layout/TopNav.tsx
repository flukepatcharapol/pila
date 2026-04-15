// =============================================================================
// components/layout/TopNav.tsx — Sticky top navigation bar
// Shows the current page title (from usePageTitle context), a branch switcher
// dropdown for owner/developer roles, and the user's avatar.
// =============================================================================

import { useContext, useState, useEffect } from 'react'
import { PageTitleContext } from '@/hooks/usePageTitle'
import { useAuth } from '@/stores/AuthContext'
import { branchesApi } from '@/api/branches'
import type { Branch } from '@/types'

export function TopNav() {
  const { title } = useContext(PageTitleContext)
  const { user, activeBranchId, setActiveBranchId } = useAuth()

  // Branch list for the switcher dropdown — only loaded for owner/developer
  const [branches, setBranches] = useState<Branch[]>([])
  const [switcherOpen, setSwitcherOpen] = useState(false)

  // Owner and developer can see all branches and switch between them
  const canSwitchBranch = user?.role === 'owner' || user?.role === 'developer'

  // Fetch branch list once when the component mounts (for switcher)
  useEffect(() => {
    if (!canSwitchBranch) return
    branchesApi.list().then(setBranches).catch(() => {})
  }, [canSwitchBranch])

  // Find the active branch name from the list for display
  const activeBranch = branches.find((b) => b.id === activeBranchId)

  return (
    <header className="sticky top-0 z-header h-16 flex items-center px-6 gap-4 bg-surface-container-lowest/80 backdrop-blur-header border-b border-outline-variant">
      {/* Page title — set by each page via usePageTitle() */}
      <h1 className="flex-1 text-title-lg font-display font-semibold text-on-surface truncate">
        {title || 'Pila Studio'}
      </h1>

      {/* Branch switcher — owner/developer only */}
      {canSwitchBranch && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setSwitcherOpen((o) => !o)}
            data-testid="topnav-branch-switcher"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-outline-variant bg-surface-container-low hover:bg-surface-container text-label-md text-on-surface transition-colors"
          >
            <svg className="w-4 h-4 text-on-surface-variant" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
            </svg>
            <span className="max-w-[140px] truncate">
              {activeBranch?.name ?? 'เลือกสาขา'}
            </span>
            <svg className="w-4 h-4 text-on-surface-variant" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown list */}
          {switcherOpen && (
            <>
              {/* Click-away backdrop */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setSwitcherOpen(false)}
                aria-hidden="true"
              />
              <ul
                className="absolute right-0 mt-1 z-20 min-w-[180px] py-1 rounded-lg border border-outline-variant bg-surface-container-lowest shadow-elevated"
                role="listbox"
                aria-label="เลือกสาขา"
              >
                {branches.map((branch) => (
                  <li key={branch.id} role="option" aria-selected={branch.id === activeBranchId}>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveBranchId(branch.id)
                        setSwitcherOpen(false)
                      }}
                      className={[
                        'w-full text-left px-3 py-2 text-body-md transition-colors',
                        branch.id === activeBranchId
                          ? 'bg-secondary/10 text-secondary font-medium'
                          : 'text-on-surface hover:bg-surface-container-low',
                      ].join(' ')}
                    >
                      {branch.name}
                    </button>
                  </li>
                ))}
                {branches.length === 0 && (
                  <li className="px-3 py-2 text-body-sm text-on-surface-variant">
                    ไม่พบสาขา
                  </li>
                )}
              </ul>
            </>
          )}
        </div>
      )}

      {/* User avatar */}
      {user && (
        <div
          className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0"
          title={user.display_name}
          aria-label={`ผู้ใช้: ${user.display_name}`}
        >
          <span className="text-on-secondary text-label-sm font-semibold">
            {user.display_name.charAt(0).toUpperCase()}
          </span>
        </div>
      )}
    </header>
  )
}

export default TopNav
