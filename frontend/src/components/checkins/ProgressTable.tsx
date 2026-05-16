import type { CheckinGoalData } from '@/types';
import { computeScore } from '@/lib/utils';

interface ProgressTableProps {
  data: CheckinGoalData[];
}

export function ProgressTable({ data }: ProgressTableProps) {
  return (
    <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Goal</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Target</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Actual</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Score</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => {
            const score = item.computed_score ?? computeScore(
              item.uom_type, item.target_value ? parseFloat(item.target_value) : null,
              item.actual_value ? parseFloat(item.actual_value) : null,
            );
            const pct = Math.round(score * 100);
            return (
              <tr key={item.goal_id} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                <td className="px-4 py-3 font-medium text-zinc-800">{item.goal_title}</td>
                <td className="px-4 py-3 text-zinc-600">{item.target_value || item.target_date || '0'}</td>
                <td className="px-4 py-3 text-zinc-600">{item.actual_value || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-semibold ${pct >= 80 ? 'text-emerald-600' : pct >= 50 ? 'text-amber-600' : 'text-red-500'}`}>
                    {pct}%
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-zinc-500">{item.status}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
