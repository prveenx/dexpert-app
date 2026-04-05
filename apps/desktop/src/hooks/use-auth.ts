import { useAuthStore } from '../stores/auth.store';
import { useCallback } from 'react';

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, clearUser, setLoading } = useAuthStore();

  const signOut = useCallback(async () => {
    try {
      await (window as any).dexpert.auth.clearToken();
      clearUser();
    } catch (error) {
      console.error('Failed to sign out:', error);
    }
  }, [clearUser]);

  const getToken = useCallback(async () => {
    try {
      return await (window as any).dexpert.auth.getToken();
    } catch (err) {
      console.error('Failed to get token:', err);
      return null;
    }
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    setUser,
    signOut,
    getToken,
    setLoading,
  };
}
