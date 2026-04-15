// =============================================================================
// components/ui/DatePicker.tsx — Date input wrapper
// Uses native <input type="date"> for browser-native calendar UI.
// Value is always an ISO date string "YYYY-MM-DD" or null for empty state.
// =============================================================================

interface DatePickerProps {
  label?: string
  value: string | null
  onChange: (value: string | null) => void
  min?: string   // ISO date "YYYY-MM-DD"
  max?: string   // ISO date "YYYY-MM-DD"
  error?: string
  required?: boolean
  disabled?: boolean
  id?: string
}

export function DatePicker({
  label,
  value,
  onChange,
  min,
  max,
  error,
  required,
  disabled,
  id,
}: DatePickerProps) {
  const inputId = id ?? (label ? `date-${label.replace(/\s+/g, '-').toLowerCase()}` : undefined)

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-label-md text-on-surface font-medium"
        >
          {label}
          {required && <span className="text-error ml-1">*</span>}
        </label>
      )}

      <input
        type="date"
        id={inputId}
        // Convert null to empty string — native date input needs '' for empty
        value={value ?? ''}
        min={min}
        max={max}
        required={required}
        disabled={disabled}
        onChange={(e) => {
          // Convert empty string back to null so callers get null on clear
          onChange(e.target.value || null)
        }}
        className={[
          'form-input w-full px-3 py-2 rounded-md text-body-md text-on-surface',
          'bg-surface-container-lowest',
          error
            ? 'border border-error focus:ring-2 focus:ring-error/20 focus:border-error'
            : 'border border-outline-variant focus:ring-2 focus:ring-secondary/20 focus:border-secondary',
          'disabled:bg-surface-container-high disabled:cursor-not-allowed',
          'outline-none transition-colors duration-150',
        ].join(' ')}
      />

      {error && (
        <p className="text-body-sm text-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default DatePicker
