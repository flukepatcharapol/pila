/**
 * App.tsx — Root component with routing and auth wiring
 *
 * Injects navigate + session-expired handler into the API client so that:
 *   - Protected-route 401s auto-redirect to /pin or /login
 *   - session_expired / session_revoked triggers the SessionExpiredModal from any page
 */

import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { setNavigate, setSessionExpiredHandler } from '@/api/client';
import { clearAllTokens, getAccessToken, isPasswordSessionValid } from '@/lib/auth';
import SessionExpiredModal from '@/components/SessionExpiredModal';
import Login from '@/pages/Login';
import Pin from '@/pages/Pin';
import Dashboard from '@/pages/Dashboard';

/**
 * ProtectedRoute — guards routes that require a valid access JWT.
 *
 * On mount: checks localStorage for access_token.
 *   - No token + valid password session → redirect /pin (re-enter PIN)
 *   - No token + no password session   → redirect /login (full re-login)
 *
 * This mirrors the client.ts 401-interceptor logic but at the routing level,
 * so routes are protected even before any API call is made.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const nav = useNavigate();

  useEffect(() => {
    // Check token on each mount (e.g. after browser back, manual URL entry)
    if (!getAccessToken()) {
      if (isPasswordSessionValid()) {
        // Password session still valid — only PIN re-entry needed
        nav('/pin', { replace: true });
      } else {
        // Both sessions gone — full re-login required
        clearAllTokens();
        nav('/login', { replace: true });
      }
    }
  }, [nav]);

  // Render null while redirect is pending (avoids flash of protected content)
  if (!getAccessToken()) return null;

  return <>{children}</>;
}

export default function App() {
  const navigate = useNavigate();
  const [sessionExpiredOpen, setSessionExpiredOpen] = useState(false);

  // Wire the API client's navigation + session-expiry callbacks once on mount.
  useEffect(() => {
    setNavigate(navigate);
    setSessionExpiredHandler(() => {
      setSessionExpiredOpen(true);
    });
  }, [navigate]);

  function handleSessionExpiredConfirm() {
    setSessionExpiredOpen(false);
    clearAllTokens();
    navigate('/login');
  }

  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/pin" element={<Pin />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        {/* Default: redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      {/* Global session-expired modal (triggered by API client on 401 session_expired/revoked) */}
      <SessionExpiredModal
        isOpen={sessionExpiredOpen}
        onConfirm={handleSessionExpiredConfirm}
      />
    </>
  );
}
