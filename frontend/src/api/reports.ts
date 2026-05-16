import client from './client';

export const reportsApi = {
  getAchievementReport: async (params?: { cycle_id?: string; quarter?: string; department?: string }) => {
    const { data } = await client.get('/reports/achievement-report', { params });
    return data;
  },
  getCompletionDashboard: async (cycleId?: string) => {
    const params = cycleId ? { cycle_id: cycleId } : {};
    const { data } = await client.get('/reports/completion-dashboard', { params });
    return data;
  },
  exportCsv: async (params?: { cycle_id?: string; department?: string }) => {
    const response = await client.get('/reports/export/csv', { params, responseType: 'blob' });
    return response.data;
  },
  exportExcel: async (params?: { cycle_id?: string; department?: string }) => {
    const response = await client.get('/reports/export/excel', { params, responseType: 'blob' });
    return response.data;
  },
  getQoQTrends: async (cycleId?: string) => {
    const params = cycleId ? { cycle_id: cycleId } : {};
    const { data } = await client.get('/reports/analytics/qoq', { params });
    return data;
  },
  getDistribution: async (cycleId?: string) => {
    const params = cycleId ? { cycle_id: cycleId } : {};
    const { data } = await client.get('/reports/analytics/distribution', { params });
    return data;
  },
};
