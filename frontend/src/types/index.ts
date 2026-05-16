export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'employee' | 'manager' | 'admin';
  department_id: string | null;
  department_name: string | null;
  manager_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  employee_count?: number | null;
}

export interface Cycle {
  id: string;
  name: string;
  goal_setting_open: string;
  q1_open: string;
  q2_open: string;
  q3_open: string;
  q4_open: string;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}

export interface GoalSheet {
  id: string;
  employee_id: string;
  cycle_id: string;
  status: 'draft' | 'submitted' | 'approved' | 'returned';
  submitted_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  is_locked: boolean;
  total_weightage: number;
  created_at: string;
  updated_at: string;
  goals: Goal[];
  employee_name?: string;
  employee_email?: string;
}

export interface Goal {
  id: string;
  goal_sheet_id: string;
  thrust_area: string;
  title: string;
  description: string | null;
  uom_type: 'min' | 'max' | 'timeline' | 'zero';
  target_value: number | null;
  target_date: string | null;
  weightage: number;
  is_shared: boolean;
  parent_goal_id: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
  achievements: GoalAchievement[];
}

export interface GoalAchievement {
  id: string;
  goal_id: string;
  cycle_id: string;
  quarter: Quarter;
  actual_value: number | null;
  completion_date: string | null;
  status: 'not_started' | 'on_track' | 'completed';
  computed_score: number | null;
  updated_at: string | null;
}

export interface CheckinComment {
  id: string;
  goal_sheet_id: string;
  quarter: Quarter;
  manager_id: string;
  comment: string;
  created_at: string;
  manager_name?: string;
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  changed_by: string;
  changed_by_name?: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  reason: string | null;
  timestamp: string;
}

export interface EscalationRule {
  id: string;
  name: string;
  trigger_event: string;
  days_threshold: number;
  notify_employee: boolean;
  notify_manager: boolean;
  notify_hr: boolean;
  is_active: boolean;
}

export type Quarter = 'q1' | 'q2' | 'q3' | 'q4' | 'annual';

export interface CheckinGoalData {
  goal_id: string;
  goal_title: string;
  thrust_area: string;
  uom_type: string;
  target_value: string | null;
  target_date: string | null;
  weightage: string;
  actual_value: string | null;
  completion_date: string | null;
  status: string;
  computed_score: number | null;
  sheet_id: string;
}

export interface TeamCheckinData {
  employee_id: string;
  employee_name: string;
  department: string;
  goals: {
    goal_id: string;
    goal_title: string;
    uom_type: string;
    target_value: string | null;
    weightage: string;
    actual_value: string | null;
    status: string;
    computed_score: number | null;
    sheet_id: string;
  }[];
}
