import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { useAuthStore } from '@/store/authStore';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import MyGoals from '@/pages/employee/MyGoals';
import MyCheckins from '@/pages/employee/MyCheckins';
import TeamGoals from '@/pages/manager/TeamGoals';
import TeamCheckins from '@/pages/manager/TeamCheckins';
import MyTeam from '@/pages/manager/MyTeam';
import CycleManager from '@/pages/admin/CycleManager';
import UserManager from '@/pages/admin/UserManager';
import EscalationManager from '@/pages/admin/EscalationManager';
import SharedGoals from '@/pages/admin/SharedGoals';
import OrgDashboard from '@/pages/admin/OrgDashboard';
import AuditLog from '@/pages/admin/AuditLog';
import Reports from '@/pages/admin/Reports';

function RoleRedirect() {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/admin" replace />;
  if (user.role === 'manager') return <Navigate to="/manager" replace />;
  return <Navigate to="/employee" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<RoleRedirect />} />
      
      {/* Employee routes */}
      <Route element={<AppShell />}>
        <Route path="/employee" element={<MyGoals />} />
        <Route path="/employee/checkins" element={<MyCheckins />} />
      </Route>

      {/* Manager routes */}
      <Route element={<AppShell />}>
        <Route path="/manager" element={<TeamGoals />} />
        <Route path="/manager/checkins" element={<TeamCheckins />} />
        <Route path="/manager/roster" element={<MyTeam />} />
      </Route>

      {/* Admin routes */}
      <Route element={<AppShell />}>
        <Route path="/admin" element={<OrgDashboard />} />
        <Route path="/admin/users" element={<UserManager />} />
        <Route path="/admin/cycles" element={<CycleManager />} />
        <Route path="/admin/escalations" element={<EscalationManager />} />
        <Route path="/admin/shared-goals" element={<SharedGoals />} />
        <Route path="/admin/reports" element={<Reports />} />
        <Route path="/admin/audit" element={<AuditLog />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
