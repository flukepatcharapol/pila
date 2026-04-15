// =============================================================================
// components/ui/FeatureGate.tsx — Feature toggle overlay (CR-04)
// Wraps feature page content. When the module is disabled by an owner/developer
// via the permission matrix, a grey overlay with a Thai message is shown
// instead of the underlying content.
// =============================================================================

import { type ReactNode } from 'react'
import { useAuth } from '@/stores/AuthContext'

interface FeatureGateProps {
  // Must match the FeatureToggle.module key returned by GET /permissions/feature-toggles
  module: string
  children: ReactNode
}

export function FeatureGate({ module, children }: FeatureGateProps) {
  const { featureToggles } = useAuth()

  // Find the toggle for this module; if not found, default to enabled
  const toggle = featureToggles.find((t) => t.module === module)
  const isEnabled = toggle ? toggle.enabled : true

  if (isEnabled) {
    // Feature is on — render children normally
    return <>{children}</>
  }

  // Feature is off — show the overlay instead of children
  // Render children behind the overlay so the layout doesn't collapse
  return (
    <div className="relative">
      {/* Children rendered behind the overlay (helps with layout stability) */}
      <div className="pointer-events-none opacity-30 select-none" aria-hidden="true">
        {children}
      </div>

      {/* Overlay — centred message on top of the dimmed content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface/80 backdrop-blur-sm rounded-lg">
        {/* Lock icon */}
        <svg
          className="w-12 h-12 text-on-surface-variant mb-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
          />
        </svg>

        <p className="text-title-md font-display font-semibold text-on-surface leading-thai">
          ฟีเจอร์นี้ไม่พร้อมใช้งาน
        </p>
        {toggle?.label && (
          <p className="text-body-sm text-on-surface-variant mt-1 leading-thai">
            {toggle.label}
          </p>
        )}
        <p className="text-body-sm text-on-surface-variant mt-1 leading-thai">
          ติดต่อผู้ดูแลระบบเพื่อเปิดใช้งาน
        </p>
      </div>
    </div>
  )
}

export default FeatureGate
