// =============================================================================
// components/ui/Input.tsx — Labelled text input with error and hint states
// Wraps native <input> to provide consistent styling across all forms.
// Error state: red border + error message below. Hint: grey hint text below.
// =============================================================================

import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export function Input({ label, error, hint, id, className = '', ...rest }: InputProps) {
  // Generate a stable ID from the label if not provided, for accessibility
  const inputId = id ?? (label ? `input-${label.replace(/\s+/g, '-').toLowerCase()}` : undefined)

  return (
    <div className="flex flex-col gap-1">
      {/* Label — only rendered if provided */}
      {label && (
        <label
          htmlFor={inputId}
          className="text-label-md text-on-surface font-medium"
        >
          {label}
          {/* Required asterisk rendered by parent via required prop */}
          {rest.required && <span className="text-error ml-1">*</span>}
        </label>
      )}

      {/* Native input — styled to match design tokens */}
      <input
        {...rest}
        id={inputId}
        className={[
          // Base layout and typography
          'w-full px-3 py-2 rounded-md text-body-md text-on-surface',
          'bg-surface-container-lowest',
          // Border: normal vs error state
          error
            ? 'border border-error focus:ring-2 focus:ring-error/20 focus:border-error'
            : 'border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary',
          // Disabled state — keep readable but visually muted
          'disabled:bg-surface-container-high disabled:text-on-surface-variant disabled:cursor-not-allowed',
          'outline-none transition-colors duration-150',
          className,
        ].join(' ')}
      />

      {/* Error message — shown below input when error is present */}
      {error && (
        <p className="text-body-sm text-error" role="alert">
          {error}
        </p>
      )}

      {/* Hint text — shown when no error */}
      {!error && hint && (
        <p className="text-body-sm text-on-surface-variant">{hint}</p>
      )}
    </div>
  )
}

export default Input
