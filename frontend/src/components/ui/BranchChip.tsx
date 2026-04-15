// =============================================================================
// components/ui/BranchChip.tsx — Branch selector pill chips (CR-02)
// Used on pages like Session Deduct and Customer Form to pre-filter dropdowns
// so only data from the selected branch is shown.
// owner/developer can change the branch; others see a read-only badge.
// =============================================================================

import type { Branch } from '@/types'

interface BranchChipProps {
  branches: Branch[]
  selected: string | null
  onChange: (branchId: string) => void
  // If readOnly, chips are not clickable (for branch-locked roles)
  readOnly?: boolean
}

export function BranchChip({ branches, selected, onChange, readOnly = false }: BranchChipProps) {
  if (branches.length === 0) return null

  return (
    <div
      className="flex flex-wrap gap-2"
      role="group"
      aria-label="เลือกสาขา"
    >
      {branches.map((branch) => {
        const isSelected = branch.id === selected

        return (
          <button
            key={branch.id}
            type="button"
            disabled={readOnly}
            onClick={() => !readOnly && onChange(branch.id)}
            aria-pressed={isSelected}
            className={[
              'px-3 py-1 rounded-full text-label-md font-medium transition-all duration-150',
              'border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary',
              isSelected
                ? // Selected: filled with secondary color
                  'bg-secondary text-on-secondary border-secondary'
                : // Unselected: ghost pill
                  'bg-surface-container-low text-on-surface border-outline-variant hover:bg-surface-container',
              readOnly ? 'cursor-default' : 'cursor-pointer',
            ].join(' ')}
          >
            {branch.name}
          </button>
        )
      })}
    </div>
  )
}

export default BranchChip
