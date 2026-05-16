import type { Goal } from '@/types';
import { Pencil, Trash2, Lock, Share2 } from 'lucide-react';

interface GoalCardProps {
  goal: Goal;
  isLocked: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  inlineEditNode?: React.ReactNode;
}

const UOM_LABELS: Record<string, string> = {
  min: 'Higher is Better',
  max: 'Lower is Better',
  timeline: 'Timeline',
  zero: 'Zero Target',
};

export function GoalCard({ goal, isLocked, onEdit, onDelete, inlineEditNode }: GoalCardProps) {
  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 hover:border-zinc-300 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[11px] text-zinc-400 uppercase tracking-wide font-medium">{goal.thrust_area}</span>
            {goal.is_shared && (
              <span className="inline-flex items-center gap-1 text-[11px] text-zinc-400">
                <Share2 className="w-3 h-3" /> Shared
              </span>
            )}
          </div>
          <h4 className="text-sm font-semibold text-zinc-900 leading-snug">{goal.title}</h4>
          {goal.description && (
            <p className="text-[13px] text-zinc-500 mt-1.5 line-clamp-2 leading-relaxed">{goal.description}</p>
          )}
        </div>

        {isLocked ? (
          <Lock className="w-4 h-4 text-zinc-300 flex-shrink-0 mt-1" />
        ) : (
          <div className="flex items-center gap-0.5 flex-shrink-0">
            {onEdit && (
              <button onClick={onEdit} className="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors">
                <Pencil className="w-3.5 h-3.5" />
              </button>
            )}
            {onDelete && (
              <button onClick={onDelete} className="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 mt-4 pt-3 border-t border-zinc-100 text-xs text-zinc-500">
        <span>{UOM_LABELS[goal.uom_type] || goal.uom_type}</span>
        {goal.target_date && <span>Due: {new Date(goal.target_date).toLocaleDateString()}</span>}
        
        {inlineEditNode ? (
          <div className="ml-auto">{inlineEditNode}</div>
        ) : (
          <>
            {goal.target_value && <span className="ml-auto">Target: {Number(goal.target_value).toLocaleString()}</span>}
            <span className="ml-3 text-sm font-semibold text-zinc-900">{Number(goal.weightage)}%</span>
          </>
        )}
      </div>
    </div>
  );
}
