import client from './client';
import type { Cycle, User, EscalationRule, AuditLog, Department } from '@/types';

export const adminApi = {
  getCycles: async (): Promise<Cycle[]> => {
    const { data } = await client.get('/admin/cycles');
    return data;
  },
  createCycle: async (cycle: Omit<Cycle, 'id' | 'is_active' | 'created_by' | 'created_at'>): Promise<Cycle> => {
    const { data } = await client.post('/admin/cycles', cycle);
    return data;
  },
  updateCycle: async (id: string, updates: Partial<Cycle>): Promise<Cycle> => {
    const { data } = await client.put(`/admin/cycles/${id}`, updates);
    return data;
  },
  activateCycle: async (id: string): Promise<Cycle> => {
    const { data } = await client.post(`/admin/cycles/${id}/activate`);
    return data;
  },
  getUsers: async (): Promise<User[]> => {
    const { data } = await client.get('/admin/users');
    return data;
  },
  createUser: async (user: { email: string; full_name: string; password: string; role: string; department_id?: string; manager_id?: string }): Promise<User> => {
    const { data } = await client.post('/admin/users', user);
    return data;
  },
  updateUser: async (id: string, updates: Partial<User>): Promise<User> => {
    const { data } = await client.put(`/admin/users/${id}`, updates);
    return data;
  },
  getDepartments: async (): Promise<Department[]> => {
    const { data } = await client.get('/admin/departments');
    return data;
  },
  createDepartment: async (name: string): Promise<Department> => {
    const { data } = await client.post('/admin/departments', { name });
    return data;
  },
  deactivateDepartment: async (id: string): Promise<Department> => {
    const { data } = await client.post(`/admin/departments/${id}/deactivate`);
    return data;
  },
  getUserSheet: async (userId: string, cycleId: string): Promise<any> => {
    const { data } = await client.get(`/admin/users/${userId}/sheet/${cycleId}`);
    return data;
  },
  getCompletionDashboard: async (cycleId?: string) => {
    const params = cycleId ? { cycle_id: cycleId } : {};
    const { data } = await client.get('/admin/completion-dashboard', { params });
    return data;
  },
  getAuditLogs: async (params?: { entity_type?: string; user_id?: string; page?: number; page_size?: number }) => {
    const { data } = await client.get('/admin/audit-logs', { params });
    return data;
  },
  pushSharedGoals: async (template: Record<string, unknown>, employeeIds: string[]) => {
    const { data } = await client.post('/admin/shared-goals/push', {
      goal_template: template,
      employee_ids: employeeIds,
    });
    return data;
  },
  getSharedGoals: async (): Promise<any[]> => {
    const { data } = await client.get('/admin/shared-goals/list');
    return data;
  },
  updateSharedGoal: async (id: string, payload: any): Promise<any> => {
    const { data } = await client.put(`/admin/shared-goals/${id}`, payload);
    return data;
  },
  getEscalationRules: async (): Promise<EscalationRule[]> => {
    const { data } = await client.get('/admin/escalation-rules');
    return data;
  },
  createEscalationRule: async (rule: Omit<EscalationRule, 'id'>): Promise<EscalationRule> => {
    const { data } = await client.post('/admin/escalation-rules', rule);
    return data;
  },
  updateEscalationRule: async (id: string, updates: Partial<EscalationRule>): Promise<EscalationRule> => {
    const { data } = await client.put(`/admin/escalation-rules/${id}`, updates);
    return data;
  },
};
