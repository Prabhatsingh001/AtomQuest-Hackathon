import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { authApi } from '@/api/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      login: async (email: string, password: string) => {
        const response = await authApi.login(email, password);
        set({
          user: response.user,
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
        });
      },

      logout: async () => {
        const token = get().accessToken;
        const refresh = get().refreshToken;
        if (token) {
          try {
            await authApi.logout(refresh);
          } catch {}
        }
        set({ user: null, accessToken: null, refreshToken: null });
      },

      refreshAccessToken: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) throw new Error('No refresh token');
        const response = await authApi.refresh(refreshToken);
        set({ accessToken: response.access_token, refreshToken: response.refresh_token });
      },

      setTokens: (access: string, refresh: string) => {
        set({ accessToken: access, refreshToken: refresh });
      },
    }),
    {
      name: 'atomquest-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
