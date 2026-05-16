import client from './client';
import type { GoalSheet, Goal } from '@/types';

export const approvalsApi = {
  getQueue: async (): Promise<GoalSheet[]> => {
    const { data } = await client.get('/approvals/queue');
    return data;
  },

  getSheet: async (sheetId: string): Promise<GoalSheet> => {
    const { data } = await client.get(`/approvals/sheet/${sheetId}`);
    return data;
  },

  inlineEdit: async (sheetId: string, goalId: string, updates: { target_value?: number; weightage?: number }): Promise<Goal> => {
    const { data } = await client.put(`/approvals/sheet/${sheetId}/goal/${goalId}`, updates);
    return data;
  },

  approve: async (sheetId: string): Promise<GoalSheet> => {
    const { data } = await client.post(`/approvals/approve/${sheetId}`);
    return data;
  },

  returnSheet: async (sheetId: string, comment: string): Promise<GoalSheet> => {
    const { data } = await client.post(`/approvals/return/${sheetId}`, { comment });
    return data;
  },

  unlock: async (sheetId: string, reason?: string): Promise<GoalSheet> => {
    const { data } = await client.post(`/approvals/unlock/${sheetId}`, { reason });
    return data;
  },
};
