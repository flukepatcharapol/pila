/**
 * Dashboard.tsx — Placeholder dashboard page
 *
 * Protected route: only accessible after PIN verify (access JWT required).
 * Provides the logout action per design doc § 8 (FE-5).
 */

import { useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { getAccessToken, clearAllTokens } from '@/lib/auth';

export default function Dashboard() {
  const navigate = useNavigate();

  async function handleLogout() {
    const token = getAccessToken();

    // POST /auth/logout — fire-and-forget; errors are intentionally ignored
    await api
      .post(
        '/auth/logout',
        {},
        { headers: { Authorization: `Bearer ${token ?? ''}` } }
      )
      .catch(() => {});

    clearAllTokens();
    navigate('/login');
  }

  return (
    <main className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div style={{ textAlign: 'center' }}>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 800,
            color: 'var(--color-primary, #162839)',
            marginBottom: '0.5rem',
          }}
        >
          Pila
        </h1>
        <p
          style={{
            color: 'var(--color-on-surface-variant, #666)',
            marginBottom: '2rem',
          }}
        >
          Studio Management System
        </p>
        <button
          onClick={() => void handleLogout()}
          style={{
            padding: '0.625rem 1.5rem',
            backgroundColor: 'var(--color-error, #b00020)',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '0.9rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          ออกจากระบบ
        </button>
      </div>
    </main>
  );
}
