import { useAuth } from '@/hooks/useAuth';
import { LogOut, Menu } from 'lucide-react';

interface TopBarProps {
  onOpenSidebar?: () => void;
}

export function TopBar({ onOpenSidebar }: TopBarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 bg-white border-b border-zinc-200 flex items-center justify-between lg:justify-end px-4 sm:px-6 gap-4 sticky top-0 z-30">
      {onOpenSidebar && (
        <button
          onClick={onOpenSidebar}
          className="lg:hidden p-2 -ml-2 text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors"
          title="Open Menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      )}
      <div className="flex items-center gap-4 ml-auto">
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
      </div>
    </header>
  );
}
