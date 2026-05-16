import client from './client';
import type { GoalSheet, Goal } from '@/types';

export const goalsApi = {
  getMySheet: async (cycleId: string): Promise<GoalSheet> => {
    const { data } = await client.get(`/goals/my-sheet/${cycleId}`);
    return data;
  },

  createGoal: async (goal: {
    goal_sheet_id: string;
    thrust_area: string;
    title: string;
    description?: string;
    uom_type: string;
    target_value?: number;
    target_date?: string;
    weightage: number;
  }): Promise<Goal> => {
    const { data } = await client.post('/goals/', goal);
    return data;
  },

  updateGoal: async (goalId: string, updates: Partial<Goal>): Promise<Goal> => {
    const { data } = await client.put(`/goals/${goalId}`, updates);
    return data;
  },

  deleteGoal: async (goalId: string) => {
    const { data } = await client.delete(`/goals/${goalId}`);
    return data;
  },

  submitSheet: async (sheetId: string): Promise<GoalSheet> => {
    const { data } = await client.post(`/goals/submit/${sheetId}`);
    return data;
  },

  getSheet: async (sheetId: string): Promise<GoalSheet> => {
    const { data } = await client.get(`/goals/sheet/${sheetId}`);
    return data;
  },
};
