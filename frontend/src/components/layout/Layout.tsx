// =============================================================================
// components/layout/Layout.tsx — App shell for all protected pages
// Provides: fixed Sidebar (left) + sticky TopNav (top) + scrollable main area.
// All providers that need to be inside ProtectedRoute but outside individual
// pages (Toast, PageTitle) are mounted here once.
// =============================================================================

import { Outlet } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopNav } from '@/components/layout/TopNav'
import { ToastContainer } from '@/components/ui/Toast'
import { ToastProvider } from '@/hooks/useToast'
import { PageTitleProvider } from '@/hooks/usePageTitle'

export function Layout() {
  return (
    // PageTitleProvider — pages call usePageTitle('...') to set the TopNav title
    <PageTitleProvider>
      {/* ToastProvider — pages call useToast().toast.success/error() */}
      <ToastProvider>
        <div className="flex min-h-screen bg-background">
          {/* Fixed sidebar — width = w-sidebar (18rem / 288px) */}
          <Sidebar />

          {/* Main content area — offset left by sidebar width */}
          <div className="flex flex-col flex-1 ml-72">
            {/* Sticky top navigation bar */}
            <TopNav />

            {/* Page content — rendered by React Router <Outlet> */}
            <main className="flex-1 p-6 md:p-8 animate-fade-in-up">
              <Outlet />
            </main>
          </div>
        </div>

        {/* Global toast stack — rendered above everything (z-toast = 80) */}
        <ToastContainer />
      </ToastProvider>
    </PageTitleProvider>
  )
}

export default Layout
