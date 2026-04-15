// =============================================================================
// hooks/usePageTitle.ts — Set the current page title shown in TopNav
// Pages call this hook to declare their title once; TopNav reads it via context.
// Using a context (not document.title) keeps the title inside the React tree
// so TopNav can animate the transition when navigating between pages.
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
// Context
// ---------------------------------------------------------------------------

interface PageTitleContextValue {
  title: string
  setTitle: (title: string) => void
}

export const PageTitleContext = createContext<PageTitleContextValue>({
  title: '',
  setTitle: () => {},
})

// Provider — rendered once inside Layout.tsx
export function PageTitleProvider({ children }: { children: ReactNode }) {
  const [title, setTitleState] = useState('')

  const setTitle = useCallback((t: string) => {
    setTitleState(t)
  }, [])

  return createElement(
    PageTitleContext.Provider,
    { value: { title, setTitle } },
    children,
  )
}

// ---------------------------------------------------------------------------
// Hook for pages — call at the top of each page component
// usePageTitle('ลูกค้า') — sets the title shown in TopNav
// ---------------------------------------------------------------------------

import { useEffect } from 'react'

export function usePageTitle(title: string): void {
  const { setTitle } = useContext(PageTitleContext)

  // Set title whenever the component mounts or the title string changes
  useEffect(() => {
    setTitle(title)
    // Clear on unmount so TopNav doesn't show a stale title briefly
    return () => setTitle('')
  }, [title, setTitle])
}
