import { NavLink } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import {
  Target, CheckSquare, Users, BarChart3, Settings,
  Shield, ClipboardList, FileText,
} from 'lucide-react';

const NAV = {
  employee: [
    { to: '/employee', icon: Target, label: 'My Goals', end: true },
    { to: '/employee/checkins', icon: CheckSquare, label: 'Check-ins' },
  ],
  manager: [
    { to: '/manager', icon: Users, label: 'Team Goals', end: true },
    { to: '/manager/checkins', icon: ClipboardList, label: 'Team Check-ins' },
    { to: '/manager/roster', icon: FileText, label: 'My Team' },
  ],
  admin: [
    { to: '/admin', icon: BarChart3, label: 'Dashboard', end: true },
    { to: '/admin/users', icon: Users, label: 'Users' },
    { to: '/admin/cycles', icon: Settings, label: 'Cycles' },
    { to: '/admin/escalations', icon: Shield, label: 'Escalations' },
    { to: '/admin/shared-goals', icon: Target, label: 'Shared Goals' },
    { to: '/admin/reports', icon: FileText, label: 'Reports' },
    { to: '/admin/audit', icon: ClipboardList, label: 'Audit Log' },
  ],
};

export function Sidebar() {
  const { user } = useAuthStore();
  if (!user) return null;

  const items = NAV[user.role] || [];

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-white border-r border-zinc-200 flex flex-col z-40">
      <div className="px-5 py-5 border-b border-zinc-100">
        <h1 className="text-base font-bold text-zinc-900 tracking-tight">AtomQuest</h1>
        <p className="text-[11px] text-zinc-400 uppercase tracking-widest mt-0.5">Goal Portal</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-100 text-zinc-900'
                  : 'text-zinc-500 hover:text-zinc-800 hover:bg-zinc-50'
              }`
            }
          >
            <item.icon className="w-[18px] h-[18px]" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
