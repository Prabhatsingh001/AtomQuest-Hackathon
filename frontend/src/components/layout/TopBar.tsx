import { useAuth } from '@/hooks/useAuth';
import { LogOut } from 'lucide-react';

export function TopBar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 bg-white border-b border-zinc-200 flex items-center justify-end px-6 gap-4">
      <div className="text-right leading-tight">
        <p className="text-sm font-medium text-zinc-800">{user?.full_name}</p>
        <p className="text-[11px] text-zinc-400 capitalize">{user?.role}</p>
      </div>
      <button
        onClick={logout}
        className="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors"
        title="Logout"
      >
        <LogOut className="w-4 h-4" />
      </button>
    </header>
  );
}
