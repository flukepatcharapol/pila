// =============================================================================
// pages/HelpPage.tsx — Role-specific user manual + FAQ + LINE QR codes
// Uses native <details>/<summary> for accordion — no JS overhead.
// Client-side search filters FAQ items without an API call.
// =============================================================================

import { useState } from 'react'
import { usePageTitle } from '@/hooks/usePageTitle'
import { useAuth } from '@/stores/AuthContext'
import { Input } from '@/components/ui/Input'
import type { Role } from '@/types'

interface FAQItem {
  question: string
  answer: string
  roles: Role[]
}

const FAQ_ITEMS: FAQItem[] = [
  { question: 'วิธีเบิกเซสชัน?', answer: 'ไปที่เมนู "เบิกเซสชัน" → เลือกสาขา → ค้นหาลูกค้า → กดปุ่ม "เบิกเซสชัน"', roles: ['admin', 'trainer', 'branch_master', 'developer', 'owner'] },
  { question: 'วิธีเพิ่มลูกค้าใหม่?', answer: 'ไปที่เมนู "ลูกค้า" → กด "+ เพิ่มลูกค้า" → กรอกข้อมูลให้ครบ → กด "เพิ่มลูกค้า"', roles: ['admin', 'branch_master', 'developer', 'owner'] },
  { question: 'วิธีสร้างคำสั่งซื้อ?', answer: 'ไปที่เมนู "คำสั่งซื้อ" → กด "+ คำสั่งซื้อใหม่" → เลือกลูกค้าและแพ็กเกจ → กรอกข้อมูลการชำระ → กด "สร้างคำสั่งซื้อ"', roles: ['admin', 'branch_master', 'developer', 'owner'] },
  { question: 'วิธีดูรายงานเทรนเนอร์?', answer: 'ไปที่เมนู "รายงานเทรนเนอร์" → เลือกช่วงวันที่ → กด "ดูรายงาน"', roles: ['admin', 'trainer', 'branch_master', 'developer', 'owner'] },
  { question: 'วิธีจองตารางฝึก?', answer: 'ไปที่เมนู "ตารางจอง" → คลิกช่องว่างในตาราง → กรอกข้อมูลลูกค้าและเทรนเนอร์ → กด "จอง"', roles: ['admin', 'branch_master', 'developer', 'owner'] },
  { question: 'ลืม PIN ต้องทำอย่างไร?', answer: 'ที่หน้า Login → กด "ลืม PIN?" → กรอกอีเมล → รับ OTP → ตั้ง PIN ใหม่', roles: ['admin', 'trainer', 'branch_master', 'developer', 'owner'] },
  { question: 'วิธีเปลี่ยนบทบาทผู้ใช้?', answer: 'ไปที่เมนู "ผู้ใช้งาน" → คลิกชื่อผู้ใช้ → เลือกบทบาทใหม่ → กด "บันทึกบทบาท"', roles: ['branch_master', 'developer', 'owner'] },
  { question: 'วิธีตั้งค่าแพ็กเกจใหม่?', answer: 'ไปที่เมนู "แพ็กเกจ" → กด "+ เพิ่มแพ็กเกจ" → กรอกชื่อ ชั่วโมง ราคา → กด "เพิ่มแพ็กเกจ"', roles: ['branch_master', 'developer', 'owner'] },
]

interface ManualSection {
  title: string
  content: string
  roles: Role[]
}

const MANUAL_SECTIONS: ManualSection[] = [
  { title: 'การเบิกเซสชัน', content: 'ระบบจะหักชั่วโมงจากยอดคงเหลือของลูกค้าทีละ 1 ชั่วโมง ต้องเลือกสาขาและลูกค้าให้ถูกต้องก่อนกดเบิก ระบบใช้ SELECT FOR UPDATE เพื่อป้องกันการเบิกซ้ำ', roles: ['admin', 'trainer', 'branch_master', 'developer', 'owner'] },
  { title: 'การจัดการลูกค้า', content: 'สามารถเพิ่ม แก้ไข และดูประวัติลูกค้าได้ รหัสลูกค้าถูกสร้างอัตโนมัติจาก prefix ของสาขา ลูกค้า 1 คนสามารถมีเทรนเนอร์และผู้ดูแลเด็กได้', roles: ['admin', 'branch_master', 'developer', 'owner'] },
  { title: 'การจัดการคำสั่งซื้อ', content: 'คำสั่งซื้อเชื่อมระหว่างลูกค้าและแพ็กเกจ สามารถบันทึกการชำระแบบผ่อนได้ ระบบคำนวณยอดค้างชำระอัตโนมัติ', roles: ['admin', 'branch_master', 'developer', 'owner'] },
  { title: 'การจัดการสิทธิ์ (Owner เท่านั้น)', content: 'Owner สามารถเปิด/ปิด Feature ต่าง ๆ และกำหนดสิทธิ์ของแต่ละ Role ได้ที่หน้า "สิทธิ์การเข้าถึง"', roles: ['owner', 'developer'] },
]

export default function HelpPage() {
  usePageTitle('ช่วยเหลือ')
  const { user } = useAuth()
  const [faqSearch, setFaqSearch] = useState('')

  const userRole = user?.role ?? 'trainer'

  // Filter FAQ by role + search query
  const filteredFAQ = FAQ_ITEMS.filter((item) =>
    item.roles.includes(userRole) &&
    (faqSearch === '' || item.question.toLowerCase().includes(faqSearch.toLowerCase()) || item.answer.toLowerCase().includes(faqSearch.toLowerCase()))
  )

  const relevantManual = MANUAL_SECTIONS.filter((s) => s.roles.includes(userRole))

  return (
    <div className="space-y-8 max-w-2xl">
      {/* User manual */}
      <section>
        <h2 className="text-title-lg font-display font-semibold text-on-surface mb-4">คู่มือการใช้งาน</h2>
        <div className="space-y-2">
          {relevantManual.map((section) => (
            <details key={section.title} className="bg-surface-container-lowest rounded-xl border border-outline-variant group">
              <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none font-medium text-on-surface">
                {section.title}
                <svg className="w-4 h-4 text-on-surface-variant transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-4 pb-4 pt-2 border-t border-outline-variant">
                <p className="text-body-md text-on-surface-variant leading-thai">{section.content}</p>
              </div>
            </details>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section>
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h2 className="text-title-lg font-display font-semibold text-on-surface">คำถามที่พบบ่อย</h2>
          <div className="w-64">
            <Input placeholder="ค้นหาคำถาม…" value={faqSearch} onChange={(e) => setFaqSearch(e.target.value)} data-testid="help-faq-search" />
          </div>
        </div>
        <div className="space-y-2">
          {filteredFAQ.length === 0 ? (
            <p className="text-body-md text-on-surface-variant py-8 text-center">ไม่พบคำถามที่ตรงกับการค้นหา</p>
          ) : filteredFAQ.map((item) => (
            <details key={item.question} className="bg-surface-container-lowest rounded-xl border border-outline-variant group">
              <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none text-body-md font-medium text-on-surface">
                {item.question}
                <svg className="w-4 h-4 text-on-surface-variant transition-transform group-open:rotate-180 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-4 pb-4 pt-2 border-t border-outline-variant">
                <p className="text-body-md text-on-surface-variant leading-thai">{item.answer}</p>
              </div>
            </details>
          ))}
        </div>
      </section>

      {/* LINE QR codes */}
      <section>
        <h2 className="text-title-lg font-display font-semibold text-on-surface mb-4">ติดต่อ Support</h2>
        <div className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient space-y-3">
          <p className="text-body-md text-on-surface-variant leading-thai">
            หากพบปัญหาการใช้งาน สามารถติดต่อผู้ดูแลระบบผ่าน LINE ได้ที่:
          </p>
          <div className="flex flex-wrap gap-4">
            <div className="flex flex-col items-center gap-2 p-3 rounded-lg border border-outline-variant">
              <div className="w-24 h-24 bg-surface-container-low rounded-lg flex items-center justify-center">
                <p className="text-label-sm text-on-surface-variant text-center">LINE QR<br/>Developer</p>
              </div>
              <p className="text-label-md font-medium text-on-surface">ผู้พัฒนาระบบ</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
