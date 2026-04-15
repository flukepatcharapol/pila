// =============================================================================
// hooks/useCurrentUser.ts — Convenience hook for components that only need
// the current user object (not the full AuthContext).
// Saves destructuring boilerplate in components that just check user.role.
// =============================================================================

import { useAuth } from '@/stores/AuthContext'
import type { CurrentUser } from '@/types'

interface UseCurrentUserResult {
  user: CurrentUser | null
  isLoading: boolean
}

// Returns the logged-in user and loading state from AuthContext.
// Components that also need activeBranchId or featureToggles should
// use useAuth() directly instead of this hook.
export function useCurrentUser(): UseCurrentUserResult {
  const { user, isLoading } = useAuth()
  return { user, isLoading }
}
