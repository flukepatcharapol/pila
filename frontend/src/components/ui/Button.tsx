// =============================================================================
// components/ui/Button.tsx — Reusable button component
// Supports 4 visual variants and 3 sizes, plus a loading state that disables
// the button and shows a spinner to prevent double-submit.
// =============================================================================

import type { ButtonHTMLAttributes, ReactNode } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  children: ReactNode
}

// ---------------------------------------------------------------------------
// Style maps — variant and size each map to a Tailwind class string
// ---------------------------------------------------------------------------

// Background, text, border, and hover styles per variant
const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-on-primary hover:bg-primary-container focus-visible:ring-primary',
  secondary:
    'bg-secondary text-on-secondary hover:bg-on-secondary-container focus-visible:ring-secondary',
  ghost:
    'bg-transparent text-on-surface border border-outline-variant hover:bg-surface-container-low focus-visible:ring-outline',
  danger:
    'bg-error text-on-error hover:opacity-90 focus-visible:ring-error',
}

// Padding and font size per size
const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-label-md',
  md: 'px-4 py-2 text-label-lg',
  lg: 'px-6 py-3 text-body-md',
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  children,
  className = '',
  ...rest
}: ButtonProps) {
  // A loading button is implicitly disabled to prevent double-submit
  const isDisabled = disabled || isLoading

  return (
    <button
      {...rest}
      disabled={isDisabled}
      className={[
        // Base styles shared by all variants
        'inline-flex items-center justify-center gap-2',
        'rounded-md font-display font-semibold',
        'transition-all duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        // Disabled / loading appearance
        isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
        // Variant-specific styles
        variantClasses[variant],
        // Size-specific padding / font
        sizeClasses[size],
        // Caller can append extra classes
        className,
      ].join(' ')}
    >
      {/* Show spinner in place of the leading icon when loading */}
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4 shrink-0"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}

export default Button
