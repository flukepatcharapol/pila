/**
 * Pin.tsx — PIN entry screen
 *
 * Submits PIN with the opaque password_session_token as Bearer.
 * Handles:
 *   - invalid_pin (401)  → inline error, stay on page
 *   - session_expired / session_revoked (401) → modal → /login
 *   - account_locked (423) → inline error
 *
 * Design doc: docs/auth_dual_session_design.md § 8.3 (FE-4)
 */

import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '@/api/client';
import {
  getPasswordSessionToken,
  storeAccessToken,
  clearAllTokens,
  isPasswordSessionValid,
} from '@/lib/auth';
import SessionExpiredModal from '@/components/SessionExpiredModal';

interface PinVerifyResponse {
  access_token: string;
  expires_in: number;
  token_type: string;
}

export default function Pin() {
  const navigate = useNavigate();

  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showExpiredModal, setShowExpiredModal] = useState(false);

  // Guard: if no valid password session, redirect to login immediately
  useEffect(() => {
    if (!isPasswordSessionValid()) {
      clearAllTokens();
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  function handleModalConfirm() {
    setShowExpiredModal(false);
    clearAllTokens();
    navigate('/login');
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const passwordSessionToken = getPasswordSessionToken();
    if (!passwordSessionToken) {
      clearAllTokens();
      setIsLoading(false);
      navigate('/login');
      return;
    }

    try {
      const data = await api.post<PinVerifyResponse>(
        '/auth/pin/verify',
        { pin },
        {
          skipAuth: true, // do NOT send the access_token here
          headers: { Authorization: `Bearer ${passwordSessionToken}` },
        }
      );

      storeAccessToken(data.access_token);
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          const code = err.errorCode;

          if (code === 'session_expired' || code === 'session_revoked') {
            // Modal: tell user to log in again
            setShowExpiredModal(true);
          } else if (code === 'invalid_pin') {
            // Inline error — stay on page, do NOT clear tokens
            setError('PIN ไม่ถูกต้อง');
          } else {
            // invalid_token or unknown — redirect to login
            clearAllTokens();
            navigate('/login');
          }
        } else if (err.status === 423) {
          setError('บัญชีถูกล็อค กรุณาติดต่อผู้ดูแลระบบ');
        } else {
          setError(err.detail ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่');
        }
      } else {
        setError('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้');
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div
          style={{
            backgroundColor: 'var(--color-surface, #fff)',
            borderRadius: '16px',
            padding: '2.5rem',
            width: '100%',
            maxWidth: '360px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
            textAlign: 'center',
          }}
        >
          {/* Title */}
          <h1
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--color-primary, #162839)',
              marginBottom: '0.5rem',
            }}
          >
            ยืนยัน PIN
          </h1>
          <p
            style={{
              color: 'var(--color-on-surface-variant, #666)',
              fontSize: '0.9rem',
              marginBottom: '2rem',
            }}
          >
            กรุณากรอก PIN เพื่อเข้าสู่ระบบ
          </p>

          <form onSubmit={handleSubmit} noValidate>
            {/* PIN input */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label htmlFor="pin" className="sr-only">
                PIN
              </label>
              <input
                id="pin"
                type="password"
                inputMode="numeric"
                pattern="[0-9]*"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                required
                autoFocus
                maxLength={8}
                placeholder="••••••"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1.5px solid var(--color-outline, #ccc)',
                  borderRadius: '8px',
                  fontSize: '1.5rem',
                  letterSpacing: '0.5rem',
                  textAlign: 'center',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Error message */}
            {error && (
              <p
                role="alert"
                style={{
                  color: 'var(--color-error, #b00020)',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                }}
              >
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || pin.length === 0}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor:
                  isLoading || pin.length === 0
                    ? 'var(--color-primary-fixed-dim, #b5c8df)'
                    : 'var(--color-primary, #162839)',
                color: 'var(--color-on-primary, #fff)',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 700,
                cursor: isLoading || pin.length === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              {isLoading ? 'กำลังตรวจสอบ…' : 'ยืนยัน'}
            </button>
          </form>

          {/* Back to login */}
          <button
            onClick={() => {
              clearAllTokens();
              navigate('/login');
            }}
            style={{
              marginTop: '1.25rem',
              background: 'none',
              border: 'none',
              color: 'var(--color-secondary, #395f94)',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            กลับหน้าเข้าสู่ระบบ
          </button>
        </div>
      </main>

      {/* Session expired modal */}
      <SessionExpiredModal isOpen={showExpiredModal} onConfirm={handleModalConfirm} />
    </>
  );
}
