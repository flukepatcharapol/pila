// =============================================================================
// components/ui/Toast.tsx — Toast notification stack
// Rendered once in Layout.tsx; reads from ToastContext populated by useToast().
// Stack appears bottom-right, stacked upward, max 3 visible at once.
// =============================================================================

import { useContext } from 'react'
import { ToastContext, type ToastVariant } from '@/hooks/useToast'

// Icon SVG paths per variant
const icons: Record<ToastVariant, string> = {
  success:
    'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
  error:
    'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z',
  info:
    'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z',
}

// Border + icon color per variant
const variantStyles: Record<ToastVariant, { border: string; icon: string; bg: string }> = {
  success: { border: 'border-tertiary', icon: 'text-tertiary',   bg: 'bg-surface-container-lowest' },
  error:   { border: 'border-error',    icon: 'text-error',      bg: 'bg-surface-container-lowest' },
  info:    { border: 'border-secondary',icon: 'text-secondary',  bg: 'bg-surface-container-lowest' },
}

export function ToastContainer() {
  const { toasts, removeToast } = useContext(ToastContext)

  if (toasts.length === 0) return null

  return (
    // Fixed bottom-right, above everything (z-toast = 80)
    <div
      className="fixed bottom-6 right-6 z-toast flex flex-col gap-3 pointer-events-none"
      role="region"
      aria-label="การแจ้งเตือน"
    >
      {toasts.map((toast) => {
        const styles = variantStyles[toast.variant]
        return (
          <div
            key={toast.id}
            className={[
              // Card styling
              'pointer-events-auto flex items-start gap-3 px-4 py-3',
              'rounded-lg border shadow-elevated animate-slide-in-right',
              'min-w-[280px] max-w-sm',
              styles.bg,
              styles.border,
            ].join(' ')}
            role="alert"
          >
            {/* Variant icon */}
            <svg
              className={`w-5 h-5 shrink-0 mt-0.5 ${styles.icon}`}
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path fillRule="evenodd" d={icons[toast.variant]} clipRule="evenodd" />
            </svg>

            {/* Message text */}
            <p className="flex-1 text-body-md text-on-surface leading-thai">
              {toast.message}
            </p>

            {/* Dismiss button */}
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="shrink-0 p-0.5 rounded text-on-surface-variant hover:text-on-surface transition-colors"
              aria-label="ปิด"
            >
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        )
      })}
    </div>
  )
}

export default ToastContainer
