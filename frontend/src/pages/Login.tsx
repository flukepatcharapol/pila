/**
 * Login.tsx — Email + password login screen
 *
 * On success: stores opaque password_session_token + expiry, redirects to /pin.
 * Design doc: docs/auth_dual_session_design.md § 8 (FE-3)
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '@/api/client';
import { storePasswordSession } from '@/lib/auth';

interface LoginResponse {
  /** Canonical field name (Approach B) */
  password_session_token?: string;
  /** Legacy / backward-compat field name — same opaque value */
  temporary_token?: string;
  /** Seconds until password session expires (e.g. 2592000 for 30 days) */
  expires_in: number;
}

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await api.post<LoginResponse>(
        '/auth/login',
        { email, password },
        { skipAuth: true }
      );

      // Prefer password_session_token; fall back to temporary_token for backward compat
      const token = data.password_session_token ?? data.temporary_token;
      if (!token) {
        setError('Login response is missing session token.');
        return;
      }

      storePasswordSession(token, data.expires_in);
      navigate('/pin');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError('อีเมลหรือรหัสผ่านไม่ถูกต้อง');
        } else if (err.status === 429) {
          setError('มีการพยายามเข้าสู่ระบบมากเกินไป กรุณาลองใหม่อีกครั้ง');
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
    <main className="min-h-screen bg-background flex items-center justify-center">
      <div
        style={{
          backgroundColor: 'var(--color-surface, #fff)',
          borderRadius: '16px',
          padding: '2.5rem',
          width: '100%',
          maxWidth: '400px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
        }}
      >
        {/* Logo / Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1
            style={{
              fontSize: '2rem',
              fontWeight: 800,
              color: 'var(--color-primary, #162839)',
              marginBottom: '0.25rem',
            }}
          >
            Pila
          </h1>
          <p style={{ color: 'var(--color-on-surface-variant, #666)', fontSize: '0.9rem' }}>
            Studio Management System
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="email"
              style={{
                display: 'block',
                marginBottom: '0.4rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-on-surface, #222)',
              }}
            >
              อีเมล
            </label>
            <input
              id="email"
              data-testid="email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="your@email.com"
              style={{
                width: '100%',
                padding: '0.625rem 0.875rem',
                border: '1.5px solid var(--color-outline, #ccc)',
                borderRadius: '8px',
                fontSize: '1rem',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="password"
              style={{
                display: 'block',
                marginBottom: '0.4rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-on-surface, #222)',
              }}
            >
              รหัสผ่าน
            </label>
            <input
              id="password"
              data-testid="password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '0.625rem 0.875rem',
                border: '1.5px solid var(--color-outline, #ccc)',
                borderRadius: '8px',
                fontSize: '1rem',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Error message */}
          {error && (
            <p
              role="alert"
              data-testid="login-error"
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
            data-testid="login-submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: isLoading
                ? 'var(--color-primary-fixed-dim, #b5c8df)'
                : 'var(--color-primary, #162839)',
              color: 'var(--color-on-primary, #fff)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: isLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? 'กำลังเข้าสู่ระบบ…' : 'เข้าสู่ระบบ'}
          </button>
        </form>
      </div>
    </main>
  );
}
