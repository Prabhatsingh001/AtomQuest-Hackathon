import type { GoalSheet } from '@/types';
import { StatusChip } from '@/components/shared/StatusChip';

interface ApprovalQueueProps {
  sheets: GoalSheet[];
  onSelect: (sheet: GoalSheet) => void;
  selectedId?: string;
}

export function ApprovalQueue({ sheets, onSelect, selectedId }: ApprovalQueueProps) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-zinc-400 uppercase tracking-wide font-semibold mb-3">Pending ({sheets.length})</p>
      {sheets.map((s) => (
        <button key={s.id} onClick={() => onSelect(s)}
          className={`w-full text-left p-4 rounded-xl border text-sm transition-all ${
            selectedId === s.id ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-200 bg-white hover:bg-zinc-50 hover:border-zinc-300'
          }`}>
          <p className="font-semibold text-zinc-800">{s.employee_name}</p>
          <div className="flex items-center gap-2 mt-1.5">
            <StatusChip status={s.status} />
            <span className="text-xs text-zinc-400">{s.goals.length} goals</span>
          </div>
        </button>
      ))}
    </div>
  );
}
