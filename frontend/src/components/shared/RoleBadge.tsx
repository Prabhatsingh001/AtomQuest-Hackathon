interface RoleBadgeProps {
  role: string;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const cls =
    role === 'admin' ? 'bg-zinc-900 text-white'
    : role === 'manager' ? 'bg-zinc-200 text-zinc-700'
    : 'bg-zinc-100 text-zinc-600';

  return (
    <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-medium capitalize leading-none ${cls}`}>
      {role}
    </span>
  );
}
