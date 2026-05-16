import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import { useCallback } from 'react';

export function useAuth() {
  const { user, accessToken, login, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = useCallback(async (email: string, password: string) => {
    await login(email, password);
    const state = useAuthStore.getState();
    if (state.user) {
      const role = state.user.role;
      if (role === 'admin') navigate('/admin');
      else if (role === 'manager') navigate('/manager');
      else navigate('/employee');
    }
  }, [login, navigate]);

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login');
  }, [logout, navigate]);

  return {
    user,
    isAuthenticated: !!accessToken,
    login: handleLogin,
    logout: handleLogout,
  };
}
