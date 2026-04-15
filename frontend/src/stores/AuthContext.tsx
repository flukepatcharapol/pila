// =============================================================================
// stores/AuthContext.tsx — Global authentication and user state
// Provides the logged-in user's profile, active branch, and feature toggles
// to the entire component tree via React Context.
//
// Architecture note: This is the only global state store needed.
// We avoid Redux/Zustand because the only truly global state is:
//   1. who is logged in (CurrentUser)
//   2. which branch is active (for branch-scoped pages)
//   3. which features are enabled (for FeatureGate components)
// =============================================================================

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { authApi } from '@/api/auth'
import { permissionsApi } from '@/api/permissions'
import type { CurrentUser, FeatureToggle } from '@/types'

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

interface AuthContextValue {
  // The logged-in user fetched from GET /auth/me; null while loading or unauthenticated
  user: CurrentUser | null

  // The branch currently selected in the UI.
  // For branch_master/admin/trainer: always equals user.branch_id (cannot change).
  // For owner/developer: can be changed via the branch switcher in TopNav.
  activeBranchId: string | null

  // Update the active branch (owner/developer only); also persists to localStorage
  setActiveBranchId: (id: string) => void

  // Feature toggles fetched from GET /permissions/feature-toggles
  // FeatureGate components read this to decide whether to show the overlay
  featureToggles: FeatureToggle[]

  // True while the initial /auth/me and /permissions/feature-toggles are loading
  isLoading: boolean

  // Re-fetch /auth/me — call after role change or profile update to sync state
  refresh: () => Promise<void>
}

// ---------------------------------------------------------------------------
// Context instance
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null)

// ---------------------------------------------------------------------------
// Provider component — wrap inside ProtectedRoute so it only mounts for auth'd users
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [activeBranchId, setActiveBranchIdState] = useState<string | null>(null)
  const [featureToggles, setFeatureToggles] = useState<FeatureToggle[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch user profile and feature toggles on mount.
  // Both fetches run in parallel to minimise loading time.
  const loadContext = useCallback(async () => {
    setIsLoading(true)
    try {
      // Fire both requests at the same time — they are independent
      const [fetchedUser, fetchedToggles] = await Promise.all([
        authApi.me(),
        // Feature toggles may return 403 for lower roles; default to empty list
        permissionsApi.getFeatureToggles().catch(() => [] as FeatureToggle[]),
      ])

      setUser(fetchedUser)
      setFeatureToggles(fetchedToggles)

      // Determine active branch:
      // - branch_master/admin/trainer are locked to their branch
      // - owner/developer can switch; restore from localStorage if previously set
      if (fetchedUser.branch_id) {
        // User is locked to a single branch — use it directly
        setActiveBranchIdState(fetchedUser.branch_id)
      } else {
        // Owner/developer: load last selected branch from localStorage
        const stored = localStorage.getItem('active_branch_id')
        setActiveBranchIdState(stored)
      }
    } catch {
      // /auth/me returning an error means the token is gone — the 401 interceptor
      // in client.ts will redirect to /login, so we just clear state here
      setUser(null)
      setFeatureToggles([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load on initial mount
  useEffect(() => {
    loadContext()
  }, [loadContext])

  // Branch switcher — only meaningful for owner/developer
  const setActiveBranchId = useCallback(
    (id: string) => {
      setActiveBranchIdState(id)
      // Persist selection so it survives page refresh
      localStorage.setItem('active_branch_id', id)
    },
    [],
  )

  const value: AuthContextValue = {
    user,
    activeBranchId,
    setActiveBranchId,
    featureToggles,
    isLoading,
    refresh: loadContext,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ---------------------------------------------------------------------------
// Hook — throws if used outside the provider to surface wiring mistakes early
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    // This means a component tried to call useAuth() outside <AuthProvider>.
    // Fix: ensure the component is rendered inside the protected route tree.
    throw new Error('useAuth() must be used inside <AuthProvider>')
  }
  return ctx
}
