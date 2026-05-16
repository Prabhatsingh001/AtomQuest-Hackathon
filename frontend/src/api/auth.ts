import client from './client';
import type { User } from '@/types';

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const { data } = await client.post('/auth/login', { email, password });
    return data;
  },

  register: async (payload: { email: string; full_name: string; password: string; department_id?: string }): Promise<User> => {
    const { data } = await client.post('/auth/register', payload);
    return data;
  },

  refresh: async (refreshToken: string) => {
    const { data } = await client.post('/auth/refresh', { refresh_token: refreshToken });
    return data;
  },

  logout: async (refreshToken?: string | null) => {
    const { data } = await client.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {});
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await client.get('/auth/me');
    return data;
  },
};
