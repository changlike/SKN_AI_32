import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    try {
      const data = await apiFetch('/api/members/session/');
      setUser(data.authenticated ? data.user : null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refreshSession(); }, [refreshSession]);

  const value = useMemo(() => ({ user, setUser, loading, refreshSession }), [user, loading, refreshSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
