// =============================================================================
// components/ui/Select.tsx — Labelled dropdown select
// Uses native <select> styled with @tailwindcss/forms class strategy.
// Per CR-01: option values are UUIDs (internal); labels are human-readable.
// =============================================================================

import type { SelectHTMLAttributes } from 'react'

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: SelectOption[]
  placeholder?: string
  error?: string
}

export function Select({
  label,
  options,
  placeholder,
  error,
  id,
  className = '',
  ...rest
}: SelectProps) {
  const selectId = id ?? (label ? `select-${label.replace(/\s+/g, '-').toLowerCase()}` : undefined)

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={selectId}
          className="text-label-md text-on-surface font-medium"
        >
          {label}
          {rest.required && <span className="text-error ml-1">*</span>}
        </label>
      )}

      <select
        {...rest}
        id={selectId}
        className={[
          'form-select w-full px-3 py-2 rounded-md text-body-md text-on-surface',
          'bg-surface-container-lowest',
          error
            ? 'border border-error focus:ring-2 focus:ring-error/20 focus:border-error'
            : 'border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary',
          'disabled:bg-surface-container-high disabled:cursor-not-allowed',
          'outline-none transition-colors duration-150',
          className,
        ].join(' ')}
      >
        {/* Empty placeholder option — selected by default when no value is set */}
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {error && (
        <p className="text-body-sm text-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default Select
