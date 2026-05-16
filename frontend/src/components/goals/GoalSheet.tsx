import type { GoalSheet as GoalSheetType } from '@/types';
import { GoalCard } from './GoalCard';
import { WeightageBar } from './WeightageBar';
import { StatusChip } from '@/components/shared/StatusChip';
import { X } from 'lucide-react';

interface GoalSheetProps {
  sheet: GoalSheetType;
  onClose: () => void;
}

export function GoalSheet({ sheet, onClose }: GoalSheetProps) {
  const totalWeightage = sheet.goals.filter(g => !g.is_shared).reduce((sum, g) => sum + Number(g.weightage), 0);

  return (
    <div className="fixed inset-y-0 right-0 w-[500px] z-50 bg-white border-l border-zinc-200 shadow-xl overflow-y-auto">
      <div className="p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-zinc-900">{sheet.employee_name}</h3>
            <div className="mt-1"><StatusChip status={sheet.status} /></div>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <WeightageBar used={totalWeightage} />
        <div className="space-y-3">
          {sheet.goals.map((goal) => (
            <GoalCard key={goal.id} goal={goal} isLocked={sheet.is_locked} />
          ))}
        </div>
      </div>
    </div>
  );
}
