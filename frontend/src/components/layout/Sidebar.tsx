// =============================================================================
// components/layout/Sidebar.tsx — Main navigation sidebar
// Role-filtered menu (CR-03): each item declares requiredRoles; items the
// current user's role is not in are hidden entirely.
// Active branch is shown in the header for all roles (CR-09).
// =============================================================================

import { useLocation, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/stores/AuthContext'
import { authApi } from '@/api/auth'
import { clearAllTokens } from '@/lib/auth'
import type { Role } from '@/types'

// ---------------------------------------------------------------------------
// Menu definition
// ---------------------------------------------------------------------------

interface MenuItem {
  label: string
  path: string
  // SVG path data for the icon
  iconPath: string
  requiredRoles: Role[]
}

// All roles — used for items visible to everyone
const ALL: Role[] = ['developer', 'owner', 'branch_master', 'admin', 'trainer']
// Management-level roles — excludes trainer
const MGMT: Role[] = ['developer', 'owner', 'branch_master', 'admin']
// Senior roles — owner and above
const SENIOR: Role[] = ['developer', 'owner', 'branch_master']

interface MenuGroup {
  groupLabel: string
  items: MenuItem[]
}

const MENU_GROUPS: MenuGroup[] = [
  {
    groupLabel: 'ภาพรวม',
    items: [
      {
        label: 'Dashboard',
        path: '/dashboard',
        iconPath:
          'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
        requiredRoles: ALL,
      },
    ],
  },
  {
    groupLabel: 'ปฏิบัติการ',
    items: [
      {
        label: 'เบิกเซสชัน',
        path: '/sessions/deduct',
        iconPath:
          'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
        requiredRoles: ALL,
      },
      {
        label: 'ตารางจอง',
        path: '/booking',
        iconPath:
          'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
        requiredRoles: ALL,
      },
    ],
  },
  {
    groupLabel: 'บันทึก',
    items: [
      {
        label: 'ลูกค้า',
        path: '/customers',
        iconPath:
          'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
        requiredRoles: ALL,
      },
      {
        label: 'คำสั่งซื้อ',
        path: '/orders',
        iconPath:
          'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
        requiredRoles: MGMT,
      },
      {
        label: 'Session Log',
        path: '/sessions/log',
        iconPath:
          'M4 6h16M4 10h16M4 14h16M4 18h16',
        requiredRoles: MGMT,
      },
      {
        label: 'รายงานเทรนเนอร์',
        path: '/sessions/trainer-report',
        iconPath:
          'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
        requiredRoles: ALL,
      },
    ],
  },
  {
    groupLabel: 'จัดการ',
    items: [
      {
        label: 'เทรนเนอร์',
        path: '/trainers',
        iconPath:
          'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
        requiredRoles: MGMT,
      },
      {
        label: 'แพ็กเกจ',
        path: '/packages',
        iconPath:
          'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
        requiredRoles: SENIOR,
      },
      {
        label: 'ผู้ดูแลเด็ก',
        path: '/caretakers',
        iconPath:
          'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
        requiredRoles: MGMT,
      },
      {
        label: 'ผู้ใช้งาน',
        path: '/users',
        iconPath:
          'M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z',
        requiredRoles: SENIOR,
      },
    ],
  },
  {
    groupLabel: 'ระบบ',
    items: [
      {
        label: 'สิทธิ์การเข้าถึง',
        path: '/permissions',
        iconPath:
          'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
        requiredRoles: SENIOR,
      },
      {
        label: 'สาขา',
        path: '/settings/branches',
        iconPath:
          'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
        requiredRoles: ['developer', 'owner'],
      },
      {
        label: 'Activity Log',
        path: '/activity-log',
        iconPath:
          'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
        requiredRoles: SENIOR,
      },
      {
        label: 'ตั้งค่า',
        path: '/settings',
        iconPath:
          'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
        requiredRoles: ALL,
      },
    ],
  },
  {
    groupLabel: 'ช่วยเหลือ',
    items: [
      {
        label: 'ช่วยเหลือ',
        path: '/help',
        iconPath:
          'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
        requiredRoles: ALL,
      },
    ],
  },
]

// ---------------------------------------------------------------------------
// Role badge — small coloured label shown next to user's name
// ---------------------------------------------------------------------------

const roleLabelMap: Record<Role, string> = {
  developer:    'Developer',
  owner:        'Owner',
  branch_master: 'Branch Master',
  admin:        'Admin',
  trainer:      'Trainer',
}

const roleColorMap: Record<Role, string> = {
  developer:    'bg-purple-100 text-purple-700',
  owner:        'bg-primary/10 text-primary',
  branch_master: 'bg-secondary/10 text-secondary',
  admin:        'bg-tertiary/10 text-tertiary',
  trainer:      'bg-surface-container-high text-on-surface-variant',
}

// ---------------------------------------------------------------------------
// Sidebar component
// ---------------------------------------------------------------------------

export function Sidebar() {
  const { user, activeBranchId } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // Filter menu groups: keep groups that have at least one visible item
  // An item is visible if the current user's role is in item.requiredRoles
  const visibleGroups = MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter(
      (item) => user && item.requiredRoles.includes(user.role),
    ),
  })).filter((group) => group.items.length > 0)

  // Determine if a nav path is currently active
  // Use startsWith so /customers/new is active when path = /customers
  function isActive(path: string): boolean {
    if (path === '/dashboard') return location.pathname === '/dashboard'
    return location.pathname.startsWith(path)
  }

  async function handleLogout() {
    try {
      await authApi.logout()
    } catch {
      // Even if the API call fails, clear local tokens and redirect
    }
    clearAllTokens()
    navigate('/login')
  }

  return (
    <aside
      className="fixed top-0 left-0 h-screen w-sidebar bg-primary flex flex-col z-sidebar overflow-hidden"
      aria-label="เมนูนำทาง"
    >
      {/* ── Header: logo + branch + role badge ── */}
      <div className="px-4 py-5 border-b border-white/10 shrink-0">
        {/* Studio name */}
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-tertiary flex items-center justify-center shrink-0">
            <span className="text-on-tertiary font-display font-bold text-sm">P</span>
          </div>
          <span className="text-on-primary font-display font-bold text-title-md tracking-tight">
            Pila Studio
          </span>
        </div>

        {/* Active branch label (CR-09) */}
        {activeBranchId && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/10">
            <svg className="w-3.5 h-3.5 text-on-primary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
            </svg>
            <span className="text-label-sm text-on-primary/80 truncate">
              {/* Branch name resolved in TopNav; here show the ID as fallback */}
              สาขาที่เลือก
            </span>
          </div>
        )}
      </div>

      {/* ── Navigation menu ── */}
      <nav
        className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin"
        aria-label="เมนูหลัก"
      >
        {visibleGroups.map((group) => (
          <div key={group.groupLabel}>
            {/* Group label */}
            <p className="px-2 mb-1 text-label-sm font-semibold text-on-primary/40 uppercase tracking-wider">
              {group.groupLabel}
            </p>

            <ul className="space-y-0.5" role="list">
              {group.items.map((item) => {
                const active = isActive(item.path)
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={[
                        'flex items-center gap-3 px-3 py-2 rounded-lg',
                        'text-label-md font-medium transition-all duration-150',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tertiary',
                        active
                          ? 'bg-white/15 text-on-primary'
                          : 'text-on-primary/60 hover:bg-white/8 hover:text-on-primary/90',
                      ].join(' ')}
                      aria-current={active ? 'page' : undefined}
                    >
                      {/* Item icon */}
                      <svg
                        className="w-4 h-4 shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={active ? 2 : 1.5}
                        aria-hidden="true"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d={item.iconPath} />
                      </svg>
                      {item.label}
                    </NavLink>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* ── Footer: user profile + logout ── */}
      <div className="px-4 py-4 border-t border-white/10 shrink-0">
        {user && (
          <div className="flex items-center gap-3 mb-3">
            {/* Avatar initials */}
            <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
              <span className="text-on-secondary text-label-sm font-semibold">
                {user.display_name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-label-md font-medium text-on-primary truncate">
                {user.display_name}
              </p>
              <span
                className={[
                  'inline-block px-1.5 py-0.5 rounded text-label-sm font-medium',
                  roleColorMap[user.role],
                ].join(' ')}
              >
                {roleLabelMap[user.role]}
              </span>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={handleLogout}
          data-testid="sidebar-logout-btn"
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-label-md text-on-primary/60 hover:bg-white/8 hover:text-on-primary transition-all duration-150"
        >
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          ออกจากระบบ
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
