import client from './client';
import type { GoalAchievement, CheckinComment, CheckinGoalData, TeamCheckinData } from '@/types';

export const checkinsApi = {
  getMy: async (cycleId: string, quarter: string): Promise<CheckinGoalData[]> => {
    const { data } = await client.get(`/checkins/my/${cycleId}/${quarter}`);
    return data;
  },

  updateAchievement: async (goalId: string, quarter: string, updates: {
    actual_value?: number;
    completion_date?: string;
    status?: string;
  }): Promise<GoalAchievement> => {
    const { data } = await client.put(`/checkins/achievement/${goalId}/${quarter}`, updates);
    return data;
  },

  getTeam: async (cycleId: string, quarter: string): Promise<TeamCheckinData[]> => {
    const { data } = await client.get(`/checkins/team/${cycleId}/${quarter}`);
    return data;
  },

  addComment: async (goalSheetId: string, quarter: string, comment: string): Promise<CheckinComment> => {
    const { data } = await client.post('/checkins/comment', {
      goal_sheet_id: goalSheetId,
      quarter,
      comment,
    });
    return data;
  },

  getComments: async (sheetId: string, quarter: string): Promise<CheckinComment[]> => {
    const { data } = await client.get(`/checkins/comments/${sheetId}/${quarter}`);
    return data;
  },
};
