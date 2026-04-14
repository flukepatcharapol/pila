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
import { clearAllTokens } from '@/lib/auth';
import SessionExpiredModal from '@/components/SessionExpiredModal';
import Login from '@/pages/Login';
import Pin from '@/pages/Pin';
import Dashboard from '@/pages/Dashboard';

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
        <Route path="/dashboard" element={<Dashboard />} />
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
