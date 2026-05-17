import { NavLink } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import {
  Target, CheckSquare, Users, BarChart3, Settings,
  Shield, ClipboardList, FileText, X,
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

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuthStore();
  if (!user) return null;

  const items = NAV[user.role] || [];

  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-screen w-56 bg-white border-r border-zinc-200 flex flex-col z-50 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0 shadow-2xl lg:shadow-none' : '-translate-x-full'
        }`}
      >
        <div className="px-5 py-5 border-b border-zinc-100 flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold text-zinc-900 tracking-tight">AtomQuest</h1>
            <p className="text-[11px] text-zinc-400 uppercase tracking-widest mt-0.5">Goal Portal</p>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
            title="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-zinc-100 text-zinc-900 font-semibold'
                    : 'text-zinc-500 hover:text-zinc-800 hover:bg-zinc-50'
                }`
              }
            >
              <item.icon className="w-[18px] h-[18px] shrink-0" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
