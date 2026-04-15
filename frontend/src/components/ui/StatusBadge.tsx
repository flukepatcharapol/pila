// =============================================================================
// components/ui/StatusBadge.tsx — Coloured status pill
// Maps status strings to colour variants. Used in list tables for customer
// status, booking status, package status, order status, etc.
// =============================================================================

export type StatusVariant = 'active' | 'inactive' | 'pending' | 'error' | 'info'

interface StatusBadgeProps {
  // Human-readable label displayed in the badge
  label: string
  variant: StatusVariant
}

// Background + text color per variant using design token classes
const variantClasses: Record<StatusVariant, string> = {
  active:   'bg-tertiary/10 text-tertiary border-tertiary/20',
  inactive: 'bg-surface-container-high text-on-surface-variant border-outline-variant',
  pending:  'bg-amber-100 text-amber-800 border-amber-200',
  error:    'bg-error-container text-on-error-container border-error/20',
  info:     'bg-secondary/10 text-secondary border-secondary/20',
}

export function StatusBadge({ label, variant }: StatusBadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center px-2 py-0.5',
        'rounded-full text-label-sm font-medium border',
        variantClasses[variant],
      ].join(' ')}
    >
      {label}
    </span>
  )
}

// Convenience: map common string values to the right variant
// Usage: <StatusBadge label="Active" variant={resolveVariant(customer.status)} />
export function resolveStatusVariant(status: string): StatusVariant {
  const map: Record<string, StatusVariant> = {
    active:    'active',
    inactive:  'inactive',
    pending:   'pending',
    confirmed: 'active',
    cancelled: 'error',
    paid:      'active',
    partial:   'pending',
    expired:   'error',
  }
  return map[status] ?? 'inactive'
}

export default StatusBadge
