import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { User, CallbackRequest } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (redirectUri?: string) => Promise<void>;
  logout: () => Promise<void>;
  handleCallback: (params: CallbackRequest) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (redirectUri?: string) => {
    const authData = await api.getAuthUrl(redirectUri);
    sessionStorage.setItem('oidc_state', authData.state);
    sessionStorage.setItem('oidc_nonce', authData.nonce);
    sessionStorage.setItem('oidc_code_verifier', authData.code_verifier);
    window.location.href = authData.auth_url;
  };

  const handleCallback = async (params: CallbackRequest) => {
    const storedState = sessionStorage.getItem('oidc_state');
    const storedVerifier = sessionStorage.getItem('oidc_code_verifier');

    if (params.state !== storedState) {
      throw new Error('Invalid state parameter');
    }

    await api.callback({
      code: params.code,
      state: params.state,
      code_verifier: storedVerifier || '',
    });

    sessionStorage.removeItem('oidc_state');
    sessionStorage.removeItem('oidc_nonce');
    sessionStorage.removeItem('oidc_code_verifier');

    await checkAuth();
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, handleCallback, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}