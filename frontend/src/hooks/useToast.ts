// =============================================================================
// hooks/useToast.ts — Global toast notification system
// Provides toast.success/error/info(message) from any component.
// Toasts auto-dismiss after 4 seconds; maximum 3 visible at once.
// =============================================================================

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { createElement } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ToastVariant = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (message: string, variant: ToastVariant) => void
  removeToast: (id: string) => void
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

export const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
})

// Provider — rendered once inside Layout.tsx
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    // Remove the toast with the given ID from the stack
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback(
    (message: string, variant: ToastVariant) => {
      const id = `toast-${Date.now()}-${Math.random()}`

      // Enforce max-3 limit: drop the oldest toast if at capacity
      setToasts((prev) => {
        const next = prev.length >= 3 ? prev.slice(1) : prev
        return [...next, { id, message, variant }]
      })

      // Auto-dismiss after 4 seconds
      setTimeout(() => removeToast(id), 4000)
    },
    [removeToast],
  )

  return createElement(
    ToastContext.Provider,
    { value: { toasts, addToast, removeToast } },
    children,
  )
}

// ---------------------------------------------------------------------------
// Hook — returns a toast object with convenience methods
// ---------------------------------------------------------------------------

interface UseToastResult {
  toast: {
    success: (message: string) => void
    error: (message: string) => void
    info: (message: string) => void
  }
}

export function useToast(): UseToastResult {
  const { addToast } = useContext(ToastContext)

  return {
    toast: {
      success: (message: string) => addToast(message, 'success'),
      error: (message: string) => addToast(message, 'error'),
      info: (message: string) => addToast(message, 'info'),
    },
  }
}
