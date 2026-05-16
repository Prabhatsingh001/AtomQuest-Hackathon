import { useState, useEffect, useCallback } from 'react';
import { checkinsApi } from '@/api/checkins';
import { adminApi } from '@/api/admin';
import { computeScore } from '@/lib/utils';
import type { CheckinGoalData, Cycle } from '@/types';
import toast from 'react-hot-toast';

const QUARTERS = ['q1', 'q2', 'q3', 'q4', 'annual'] as const;
const inputCls = "px-2.5 py-1.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";
const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function MyCheckins() {
  const [quarter, setQuarter] = useState<string>('q1');
  const [checkins, setCheckins] = useState<CheckinGoalData[]>([]);
  const [cycle, setCycle] = useState<Cycle | null>(null);
  const [loading, setLoading] = useState(true);
  const [comments, setComments] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const cycles = await adminApi.getCycles().catch(() => []);
      const active = cycles.find((c: Cycle) => c.is_active);
      if (!active) { setLoading(false); return; }
      setCycle(active);
      const data = await checkinsApi.getMy(active.id, quarter);
      setCheckins(data);
      if (data.length > 0) {
        const cmts = await checkinsApi.getComments(data[0].sheet_id, quarter).catch(() => []);
        setComments(cmts);
      }
    } catch (err: any) {
      if (err.response?.status !== 403) toast.error('Failed to load');
    } finally { setLoading(false); }
  }, [quarter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleUpdate = async (goalId: string, field: string, value: any) => {
    try {
      const updates: any = {};
      if (field === 'actual_value') updates.actual_value = value;
      if (field === 'status') updates.status = value;
      if (field === 'completion_date') updates.completion_date = value;
      await checkinsApi.updateAchievement(goalId, quarter, updates);
      toast.success('Saved');
      fetchData();
    } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-bold text-zinc-900">My Check-ins</h1>
        {cycle && <p className="text-sm text-zinc-400 mt-0.5">{cycle.name}</p>}
      </div>

      {/* Quarter tabs */}
      <div className="flex gap-1 border-b border-zinc-200">
        {QUARTERS.map((q) => (
          <button key={q} onClick={() => setQuarter(q)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              quarter === q ? 'border-zinc-900 text-zinc-900' : 'border-transparent text-zinc-400 hover:text-zinc-600'
            }`}>
            {q.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Manager feedback */}
      {comments.length > 0 && (
        <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-3">
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">Manager Feedback</p>
          {comments.map((c: any) => (
            <div key={c.id}>
              <p className="text-sm text-zinc-700 leading-relaxed">{c.comment}</p>
              <p className="text-xs text-zinc-400 mt-1">{c.manager_name} · {new Date(c.created_at).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-14 animate-pulse" />)}</div>
      ) : checkins.length === 0 ? (
        <p className="text-center py-16 text-zinc-400 text-sm">No goals for this quarter</p>
      ) : (
        <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={thCls}>Goal</th>
                <th className={thCls}>Target</th>
                <th className={thCls}>Actual</th>
                <th className={thCls}>Status</th>
                <th className={thCls}>Score</th>
              </tr>
            </thead>
            <tbody>
              {checkins.map((item) => {
                const score = item.computed_score ?? computeScore(
                  item.uom_type, item.target_value ? parseFloat(item.target_value) : null,
                  item.actual_value ? parseFloat(item.actual_value) : null,
                  item.target_date, item.completion_date
                );
                const pct = Math.round(score * 100);
                return (
                  <tr key={item.goal_id} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                    <td className="px-4 py-3.5">
                      <p className="font-medium text-zinc-800">{item.goal_title}</p>
                      <p className="text-xs text-zinc-400 mt-0.5">{item.thrust_area} · {item.uom_type}</p>
                    </td>
                    <td className="px-4 py-3.5 text-zinc-600">{item.target_value || item.target_date || '0'}</td>
                    <td className="px-4 py-3.5">
                      {item.uom_type === 'timeline' ? (
                        <input type="date" className={`${inputCls} w-36`} value={item.completion_date || ''}
                          onChange={(e) => handleUpdate(item.goal_id, 'completion_date', e.target.value)} />
                      ) : (
                        <input type="number" className={`${inputCls} w-24`} value={item.actual_value || ''} step="0.01"
                          onBlur={(e) => handleUpdate(item.goal_id, 'actual_value', parseFloat(e.target.value) || 0)}
                          onChange={(e) => setCheckins(checkins.map(c => c.goal_id === item.goal_id ? { ...c, actual_value: e.target.value } : c))} />
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <select className={`${inputCls} w-32 cursor-pointer`} value={item.status}
                        onChange={(e) => handleUpdate(item.goal_id, 'status', e.target.value)}>
                        <option value="not_started">Not Started</option>
                        <option value="on_track">On Track</option>
                        <option value="completed">Completed</option>
                      </select>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-14 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-400'}`}
                            style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs font-semibold text-zinc-600 tabular-nums w-8">{pct}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
