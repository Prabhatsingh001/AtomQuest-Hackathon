import client from './client';
import type { User } from '@/types';

export const usersApi = {
  getMe: async (): Promise<User> => {
    const { data } = await client.get('/users/me');
    return data;
  },
  
  getTeam: async (): Promise<User[]> => {
    const { data } = await client.get('/users/team');
    return data;
  },
};
