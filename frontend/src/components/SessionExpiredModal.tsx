/**
 * SessionExpiredModal.tsx
 *
 * Dialog shown when the password session has expired or been revoked server-side.
 * Confirms to the user and redirects to /login on OK.
 *
 * Design doc: docs/auth_dual_session_design.md § 8.3 (error_code session_expired / session_revoked)
 */

interface SessionExpiredModalProps {
  isOpen: boolean;
  onConfirm: () => void;
}

export default function SessionExpiredModal({ isOpen, onConfirm }: SessionExpiredModalProps) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      data-testid="session-expired-modal"
      aria-modal="true"
      aria-labelledby="session-expired-title"
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 9999,
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-surface, #fff)',
          borderRadius: '12px',
          padding: '2rem',
          maxWidth: '360px',
          width: '90%',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          textAlign: 'center',
        }}
      >
        <h2
          id="session-expired-title"
          style={{
            color: 'var(--color-primary, #162839)',
            fontSize: '1.25rem',
            fontWeight: 700,
            marginBottom: '0.75rem',
          }}
        >
          Session หมดอายุ
        </h2>
        <p
          style={{
            color: 'var(--color-on-surface, #333)',
            marginBottom: '1.5rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-line',
          }}
        >
          {'Session ของท่านหมดอายุแล้ว\nกรุณาเข้าสู่ระบบใหม่'}
        </p>
        <button
          data-testid="session-expired-confirm"
          onClick={onConfirm}
          style={{
            backgroundColor: 'var(--color-primary, #162839)',
            color: 'var(--color-on-primary, #fff)',
            border: 'none',
            borderRadius: '8px',
            padding: '0.625rem 2rem',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            width: '100%',
          }}
        >
          ตกลง
        </button>
      </div>
    </div>
  );
}
