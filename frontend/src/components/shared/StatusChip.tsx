interface StatusChipProps {
  status: string;
}

const LABELS: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-zinc-100 text-zinc-600' },
  submitted: { label: 'Submitted', className: 'bg-blue-50 text-blue-700' },
  approved: { label: 'Approved', className: 'bg-emerald-50 text-emerald-700' },
  returned: { label: 'Returned', className: 'bg-amber-50 text-amber-700' },
  not_started: { label: 'Not Started', className: 'bg-zinc-100 text-zinc-500' },
  on_track: { label: 'On Track', className: 'bg-blue-50 text-blue-700' },
  completed: { label: 'Completed', className: 'bg-emerald-50 text-emerald-700' },
};

export function StatusChip({ status }: StatusChipProps) {
  const config = LABELS[status] || { label: status, className: 'bg-zinc-100 text-zinc-600' };
  return (
    <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-medium leading-none ${config.className}`}>
      {config.label}
    </span>
  );
}
