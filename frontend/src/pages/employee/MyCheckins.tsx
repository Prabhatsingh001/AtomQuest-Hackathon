import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { checkinsApi } from '@/api/checkins';
import { adminApi } from '@/api/admin';
import { computeScore } from '@/lib/utils';
import type { CheckinGoalData, Cycle } from '@/types';
import toast from 'react-hot-toast';

const QUARTERS = ['q1', 'q2', 'q3', 'q4', 'annual'] as const;
const inputCls = "px-2.5 py-1.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";
const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function MyCheckins() {
    const queryClient = useQueryClient();
    const [quarter, setQuarter] = useState<string>('q1');
    const [localCheckins, setLocalCheckins] = useState<CheckinGoalData[]>([]);

    const { data: cyclesData = [], isLoading: loadingCycles } = useQuery({
        queryKey: ['cycles'],
        queryFn: () => adminApi.getCycles().catch(() => []),
        staleTime: 1000 * 60 * 2,
    });

    const activeCycle = cyclesData.find((c: Cycle) => c.is_active);

    const { data: checkinsData = [], isLoading: loadingCheckins } = useQuery({
        queryKey: ['myCheckins', activeCycle?.id, quarter],
        queryFn: () => activeCycle ? checkinsApi.getMy(activeCycle.id, quarter) : [],
        enabled: !!activeCycle,
        staleTime: 1000 * 60 * 2,
    });

    const sheetId = checkinsData[0]?.sheet_id;

    const { data: comments = [] } = useQuery({
        queryKey: ['checkinComments', sheetId, quarter],
        queryFn: () => sheetId ? checkinsApi.getComments(sheetId, quarter).catch(() => []) : [],
        enabled: !!sheetId,
        staleTime: 1000 * 60 * 2,
    });

    useEffect(() => {
        setLocalCheckins(checkinsData);
    }, [checkinsData]);

    const loading = loadingCycles || loadingCheckins;

    const handleUpdate = async (goalId: string, field: string, value: any) => {
        try {
            const updates: any = {};
            if (field === 'actual_value') updates.actual_value = value;
            if (field === 'status') updates.status = value;
            if (field === 'completion_date') updates.completion_date = value;
            await checkinsApi.updateAchievement(goalId, quarter, updates);
            toast.success('Saved');
            queryClient.invalidateQueries({ queryKey: ['myCheckins'] });
        } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-lg font-bold text-zinc-900">My Check-ins</h1>
                {activeCycle && <p className="text-sm text-zinc-400 mt-0.5">{activeCycle.name}</p>}
            </div>

            {/* Quarter tabs */}
            <div className="flex gap-1 border-b border-zinc-200 overflow-x-auto pb-1">
                {QUARTERS.map((q) => (
                    <button key={q} onClick={() => setQuarter(q)}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors shrink-0 ${quarter === q ? 'border-zinc-900 text-zinc-900 font-semibold' : 'border-transparent text-zinc-400 hover:text-zinc-600'
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
                <div className="space-y-3">{[1, 2, 3].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-14 animate-pulse" />)}</div>
            ) : localCheckins.length === 0 ? (
                <p className="text-center py-16 text-zinc-400 text-sm">No goals for this quarter</p>
            ) : (
                <div className="bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full">
                    <table className="w-full text-sm min-w-[600px]">
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
                            {localCheckins.map((item) => {
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
                                            <span className="text-xs text-zinc-400 mt-0.5 block">{item.thrust_area}</span>
                                        </td>
                                        <td className="px-4 py-3.5 font-mono text-zinc-600">
                                            {item.uom_type === 'timeline' ? (item.target_date || '-') : (item.target_value || '-')}
                                        </td>
                                        <td className="px-4 py-3.5">
                                            {item.uom_type === 'timeline' ? (
                                                <input type="date" className={`${inputCls} w-36`} value={item.completion_date || ''}
                                                    onChange={(e) => handleUpdate(item.goal_id, 'completion_date', e.target.value)} />
                                            ) : (
                                                <input type="number" className={`${inputCls} w-24`} value={item.actual_value || ''} step="0.01"
                                                    onBlur={(e) => handleUpdate(item.goal_id, 'actual_value', parseFloat(e.target.value) || 0)}
                                                    onChange={(e) => setLocalCheckins(localCheckins.map(c => c.goal_id === item.goal_id ? { ...c, actual_value: e.target.value } : c))} />
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
                                                <div className="w-12 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                                                    <div className={`h-full rounded-full ${pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-400'}`}
                                                        style={{ width: `${pct}%` }} />
                                                </div>
                                                <span className="text-xs font-semibold text-zinc-600 tabular-nums">{pct}%</span>
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
