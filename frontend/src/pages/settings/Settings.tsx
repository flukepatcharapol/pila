// =============================================================================
// pages/settings/Settings.tsx — User preferences + Google Drive integration
// =============================================================================

import { useState, useEffect } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/stores/AuthContext'
import { settingsApi } from '@/api/settings'
import { Button } from '@/components/ui/Button'
import type { Settings as SettingsType } from '@/types'

export default function Settings() {
  usePageTitle('ตั้งค่า')
  const { toast } = useToast()
  const { user } = useAuth()

  const [settings, setSettings]     = useState<SettingsType | null>(null)
  const [darkMode, setDarkMode]     = useState(false)
  const [language, setLanguage]     = useState<'th' | 'en'>('th')
  const [googleConnected, setGoogleConnected] = useState(false)
  const [driveUsed, setDriveUsed]   = useState<number | null>(null)
  const [driveTotal, setDriveTotal] = useState<number | null>(null)
  const [isSaving, setIsSaving]     = useState(false)

  useEffect(() => {
    settingsApi.get().then((s) => {
      setSettings(s)
      setDarkMode(s.dark_mode)
      setLanguage(s.language)
      setGoogleConnected(s.google_connected)
      setDriveUsed(s.google_drive_used_bytes)
      setDriveTotal(s.google_drive_total_bytes)
    }).catch(() => {})
  }, [])

  // Apply dark mode to <html> element
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  async function handleSave() {
    setIsSaving(true)
    try {
      await settingsApi.update({ language, dark_mode: darkMode })
      toast.success('บันทึกการตั้งค่าสำเร็จ')
    } catch { toast.error('บันทึกไม่สำเร็จ') }
    finally { setIsSaving(false) }
  }

  async function handleDisconnectGoogle() {
    try {
      await settingsApi.disconnectGoogle()
      setGoogleConnected(false)
      toast.success('ยกเลิกการเชื่อมต่อ Google แล้ว')
    } catch { toast.error('ยกเลิกการเชื่อมต่อไม่สำเร็จ') }
  }

  function formatBytes(bytes: number): string {
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
    return `${(bytes / 1e6).toFixed(0)} MB`
  }

  const drivePercent = driveUsed && driveTotal ? Math.round((driveUsed / driveTotal) * 100) : null

  return (
    <div className="space-y-6 max-w-lg">
      {/* Profile (read-only) */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-3">
        <h3 className="text-title-sm font-semibold text-on-surface">โปรไฟล์</h3>
        <div className="grid grid-cols-2 gap-3 text-body-sm">
          <div><p className="text-on-surface-variant">ชื่อที่แสดง</p><p className="font-medium text-on-surface">{user?.display_name}</p></div>
          <div><p className="text-on-surface-variant">อีเมล</p><p className="font-medium text-on-surface">{user?.email}</p></div>
          <div><p className="text-on-surface-variant">บทบาท</p><p className="font-medium text-on-surface capitalize">{user?.role}</p></div>
        </div>
      </section>

      {/* Preferences */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">การแสดงผล</h3>

        {/* Language toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-surface">ภาษา</p>
            <p className="text-body-sm text-on-surface-variant">Language</p>
          </div>
          <div className="flex rounded-lg border border-outline-variant overflow-hidden">
            {(['th', 'en'] as const).map((l) => (
              <button key={l} type="button" onClick={() => setLanguage(l)}
                className={`px-4 py-1.5 text-label-md transition-colors ${language === l ? 'bg-secondary text-on-secondary' : 'text-on-surface-variant hover:bg-surface-container-low'}`}>
                {l === 'th' ? 'ไทย' : 'EN'}
              </button>
            ))}
          </div>
        </div>

        {/* Dark mode toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-body-md text-on-surface">โหมดมืด</p>
            <p className="text-body-sm text-on-surface-variant">Dark mode</p>
          </div>
          <button type="button" onClick={() => setDarkMode((d) => !d)}
            className={`relative w-12 h-6 rounded-full transition-colors ${darkMode ? 'bg-secondary' : 'bg-surface-container-high'}`}
            data-testid="settings-dark-mode-toggle">
            <span className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${darkMode ? 'translate-x-7' : 'translate-x-1'}`} />
          </button>
        </div>

        <Button variant="primary" onClick={handleSave} isLoading={isSaving} data-testid="settings-save-btn">บันทึกการตั้งค่า</Button>
      </section>

      {/* Google Drive */}
      <section className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-4">
        <h3 className="text-title-sm font-semibold text-on-surface">Google Drive</h3>
        {googleConnected ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-tertiary" />
              <p className="text-body-md text-on-surface">เชื่อมต่อแล้ว</p>
            </div>
            {drivePercent !== null && (
              <div className="space-y-1">
                <div className="flex justify-between text-body-sm text-on-surface-variant">
                  <span>ใช้ไป {formatBytes(driveUsed!)}</span>
                  <span>{formatBytes(driveTotal!)}</span>
                </div>
                <div className="h-2 rounded-full bg-surface-container-high overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${drivePercent > 80 ? 'bg-error' : 'bg-tertiary'}`} style={{ width: `${drivePercent}%` }} />
                </div>
                <p className="text-body-sm text-on-surface-variant text-right">{drivePercent}%</p>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={handleDisconnectGoogle} data-testid="settings-disconnect-google-btn">ยกเลิกการเชื่อมต่อ</Button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-body-md text-on-surface-variant leading-thai">เชื่อมต่อ Google เพื่อใช้งาน Signature Print</p>
            <Button variant="secondary" data-testid="settings-connect-google-btn"
              onClick={() => toast.info('กรุณาติดต่อผู้ดูแลระบบเพื่อเชื่อมต่อ Google')}>
              เชื่อมต่อ Google Account
            </Button>
          </div>
        )}
      </section>
    </div>
  )
}
