import client from './client';
import type { Department } from '@/types';

export const departmentsApi = {
  listActive: async (): Promise<Department[]> => {
    const { data } = await client.get('/departments');
    return data;
  },
};
