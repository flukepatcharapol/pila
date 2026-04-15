/**
 * App.tsx — Root component: routing, auth wiring, and session modal
 *
 * Route structure:
 *   /login, /pin          — public (no auth required)
 *   everything else       — protected: requires valid access_token
 *                           wrapped in AuthProvider + Layout shell
 *
 * Auth flow reminder:
 *   login  → stores password_session_token (30 days)
 *   /pin   → exchanges PIN for access_token (JWT, 6 hours)
 *   401    → API client redirects to /pin or /login depending on session state
 */

import { lazy, Suspense, useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { setNavigate, setSessionExpiredHandler } from '@/api/client'
import { clearAllTokens, getAccessToken, isPasswordSessionValid } from '@/lib/auth'
import { AuthProvider } from '@/stores/AuthContext'
import Layout from '@/components/layout/Layout'
import SessionExpiredModal from '@/components/SessionExpiredModal'

// ── Public pages (small, load eagerly) ──────────────────────────────────────
import Login from '@/pages/Login'
import Pin from '@/pages/Pin'

// ── Protected pages (lazy-loaded to keep initial bundle small) ──────────────
// Dashboard
const Dashboard = lazy(() => import('@/pages/Dashboard'))

// Customers
const CustomerList   = lazy(() => import('@/pages/customers/CustomerList'))
const CustomerForm   = lazy(() => import('@/pages/customers/CustomerForm'))
const CustomerDetail = lazy(() => import('@/pages/customers/CustomerDetail'))

// Orders
const OrderList   = lazy(() => import('@/pages/orders/OrderList'))
const OrderForm   = lazy(() => import('@/pages/orders/OrderForm'))
const OrderDetail = lazy(() => import('@/pages/orders/OrderDetail'))

// Sessions
const SessionDeduct  = lazy(() => import('@/pages/sessions/SessionDeduct'))
const SessionLog     = lazy(() => import('@/pages/sessions/SessionLog'))
const TrainerReport  = lazy(() => import('@/pages/sessions/TrainerReport'))

// Trainers
const TrainerList = lazy(() => import('@/pages/trainers/TrainerList'))
const TrainerForm = lazy(() => import('@/pages/trainers/TrainerForm'))

// Packages
const PackageList = lazy(() => import('@/pages/packages/PackageList'))
const PackageForm = lazy(() => import('@/pages/packages/PackageForm'))

// Caretakers
const CaretakerList = lazy(() => import('@/pages/caretakers/CaretakerList'))
const CaretakerForm = lazy(() => import('@/pages/caretakers/CaretakerForm'))

// Booking
const BookingSchedule = lazy(() => import('@/pages/booking/BookingSchedule'))

// Users
const UserManagement = lazy(() => import('@/pages/users/UserManagement'))

// Admin / Settings
const PermissionMatrix = lazy(() => import('@/pages/permissions/PermissionMatrix'))
const BranchConfig     = lazy(() => import('@/pages/settings/BranchConfig'))
const Settings         = lazy(() => import('@/pages/settings/Settings'))
const ActivityLog      = lazy(() => import('@/pages/ActivityLog'))
const HelpPage         = lazy(() => import('@/pages/HelpPage'))

// ── Page loading fallback ────────────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

// ── ProtectedRoute ────────────────────────────────────────────────────────────
/**
 * Guards all routes that require a valid access JWT.
 *
 * Logic on each mount:
 *   - No access_token + password_session valid → send to /pin (re-enter PIN)
 *   - No access_token + no password_session    → send to /login (full re-login)
 *   - Has access_token                         → render children
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const nav = useNavigate()

  useEffect(() => {
    if (!getAccessToken()) {
      if (isPasswordSessionValid()) {
        nav('/pin', { replace: true })
      } else {
        clearAllTokens()
        nav('/login', { replace: true })
      }
    }
  }, [nav])

  // Render null while redirect fires to avoid flashing protected content
  if (!getAccessToken()) return null
  return <>{children}</>
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const navigate = useNavigate()
  const [sessionExpiredOpen, setSessionExpiredOpen] = useState(false)

  // Wire the API client's navigate + session-expired callbacks once on mount.
  // These are called from inside client.ts when a 401 response arrives.
  useEffect(() => {
    setNavigate(navigate)
    setSessionExpiredHandler(() => setSessionExpiredOpen(true))
  }, [navigate])

  function handleSessionExpiredConfirm() {
    setSessionExpiredOpen(false)
    clearAllTokens()
    navigate('/login')
  }

  return (
    <>
      <Routes>
        {/* ── Public routes ── */}
        <Route path="/login" element={<Login />} />
        <Route path="/pin"   element={<Pin />} />

        {/* ── Protected routes — all inside AuthProvider + Layout shell ── */}
        <Route
          element={
            <ProtectedRoute>
              <AuthProvider>
                <Layout />
              </AuthProvider>
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />

          {/* Customers */}
          <Route path="/customers"          element={<Suspense fallback={<PageLoader />}><CustomerList /></Suspense>} />
          <Route path="/customers/new"      element={<Suspense fallback={<PageLoader />}><CustomerForm /></Suspense>} />
          <Route path="/customers/:id"      element={<Suspense fallback={<PageLoader />}><CustomerDetail /></Suspense>} />
          <Route path="/customers/:id/edit" element={<Suspense fallback={<PageLoader />}><CustomerForm /></Suspense>} />

          {/* Orders */}
          <Route path="/orders"          element={<Suspense fallback={<PageLoader />}><OrderList /></Suspense>} />
          <Route path="/orders/new"      element={<Suspense fallback={<PageLoader />}><OrderForm /></Suspense>} />
          <Route path="/orders/:id"      element={<Suspense fallback={<PageLoader />}><OrderDetail /></Suspense>} />
          <Route path="/orders/:id/edit" element={<Suspense fallback={<PageLoader />}><OrderForm /></Suspense>} />

          {/* Sessions */}
          <Route path="/sessions/deduct"         element={<Suspense fallback={<PageLoader />}><SessionDeduct /></Suspense>} />
          <Route path="/sessions/log"            element={<Suspense fallback={<PageLoader />}><SessionLog /></Suspense>} />
          <Route path="/sessions/trainer-report" element={<Suspense fallback={<PageLoader />}><TrainerReport /></Suspense>} />

          {/* Trainers */}
          <Route path="/trainers"          element={<Suspense fallback={<PageLoader />}><TrainerList /></Suspense>} />
          <Route path="/trainers/new"      element={<Suspense fallback={<PageLoader />}><TrainerForm /></Suspense>} />
          <Route path="/trainers/:id/edit" element={<Suspense fallback={<PageLoader />}><TrainerForm /></Suspense>} />

          {/* Packages */}
          <Route path="/packages"          element={<Suspense fallback={<PageLoader />}><PackageList /></Suspense>} />
          <Route path="/packages/new"      element={<Suspense fallback={<PageLoader />}><PackageForm /></Suspense>} />
          <Route path="/packages/:id/edit" element={<Suspense fallback={<PageLoader />}><PackageForm /></Suspense>} />

          {/* Caretakers */}
          <Route path="/caretakers"          element={<Suspense fallback={<PageLoader />}><CaretakerList /></Suspense>} />
          <Route path="/caretakers/new"      element={<Suspense fallback={<PageLoader />}><CaretakerForm /></Suspense>} />
          <Route path="/caretakers/:id/edit" element={<Suspense fallback={<PageLoader />}><CaretakerForm /></Suspense>} />

          {/* Booking */}
          <Route path="/booking" element={<Suspense fallback={<PageLoader />}><BookingSchedule /></Suspense>} />

          {/* Users */}
          <Route path="/users" element={<Suspense fallback={<PageLoader />}><UserManagement /></Suspense>} />

          {/* Admin / Settings */}
          <Route path="/permissions"        element={<Suspense fallback={<PageLoader />}><PermissionMatrix /></Suspense>} />
          <Route path="/settings/branches"  element={<Suspense fallback={<PageLoader />}><BranchConfig /></Suspense>} />
          <Route path="/settings"           element={<Suspense fallback={<PageLoader />}><Settings /></Suspense>} />
          <Route path="/activity-log"       element={<Suspense fallback={<PageLoader />}><ActivityLog /></Suspense>} />
          <Route path="/help"               element={<Suspense fallback={<PageLoader />}><HelpPage /></Suspense>} />

          {/* Fallback inside protected area → dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>

        {/* Root redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>

      {/* Global session-expired modal — triggered by 401 interceptor in client.ts */}
      <SessionExpiredModal
        isOpen={sessionExpiredOpen}
        onConfirm={handleSessionExpiredConfirm}
      />
    </>
  )
}
