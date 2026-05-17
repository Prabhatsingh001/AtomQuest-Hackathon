import { Fragment, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { checkinsApi } from '@/api/checkins';
import { adminApi } from '@/api/admin';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { Cycle } from '@/types';
import toast from 'react-hot-toast';

const QUARTERS = ['q1', 'q2', 'q3', 'q4', 'annual'] as const;
const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function TeamCheckins() {
    const [quarter, setQuarter] = useState<string>('q1');
    const [expanded, setExpanded] = useState<string | null>(null);
    const [commentText, setCommentText] = useState('');
    const [submittingComment, setSubmittingComment] = useState(false);

    const { data: cyclesData = [], isLoading: loadingCycles } = useQuery({
        queryKey: ['cycles'],
        queryFn: () => adminApi.getCycles().catch(() => []),
        staleTime: 1000 * 60 * 2,
    });

    const activeCycle = cyclesData.find((c: Cycle) => c.is_active);

    const { data: team = [], isLoading: loadingTeam } = useQuery({
        queryKey: ['teamCheckins', activeCycle?.id, quarter],
        queryFn: () => activeCycle ? checkinsApi.getTeam(activeCycle.id, quarter) : [],
        enabled: !!activeCycle,
        staleTime: 1000 * 60 * 2,
    });

    const loading = loadingCycles || loadingTeam;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-lg font-bold text-zinc-900">Team Check-ins</h1>
                {activeCycle && <p className="text-sm text-zinc-400 mt-0.5">{activeCycle.name}</p>}
            </div>

            <div className="flex gap-1 border-b border-zinc-200 overflow-x-auto pb-1">
                {QUARTERS.map((q) => (
                    <button key={q} onClick={() => setQuarter(q)}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors shrink-0 ${quarter === q ? 'border-zinc-900 text-zinc-900 font-semibold' : 'border-transparent text-zinc-400 hover:text-zinc-600'
                            }`}>{q.toUpperCase()}</button>
                ))}
            </div>

            {loading ? <div className="bg-zinc-100 rounded-xl h-48 animate-pulse" /> :
                team.length === 0 ? <p className="text-center py-16 text-zinc-400 text-sm">No data</p> : (
                    <div className="bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full">
                        <table className="w-full text-sm min-w-[500px]">
                            <thead><tr><th className={thCls}>Employee</th><th className={thCls}>Goals</th><th className={thCls}>Avg Score</th><th className={`${thCls} w-10`}></th></tr></thead>
                            <tbody>
                                {team.map((emp) => {
                                    const scores = emp.goals.filter(g => g.computed_score !== null).map(g => g.computed_score!);
                                    const avg = scores.length ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100) : 0;
                                    const open = expanded === emp.employee_id;
                                    return (
                                        <Fragment key={`${emp.employee_id}-${quarter}`}>
                                            <tr className="cursor-pointer border-b border-zinc-100 hover:bg-zinc-50/60 transition-colors"
                                                onClick={() => { setExpanded(open ? null : emp.employee_id); setCommentText(''); }}>
                                                <td className="px-4 py-3.5">
                                                    <p className="font-medium text-zinc-800">{emp.employee_name}</p>
                                                    <p className="text-xs text-zinc-400 mt-0.5">{(emp.department as any)?.name || (typeof emp.department === 'string' ? emp.department : '-')}</p>
                                                </td>
                                                <td className="px-4 py-3.5 text-zinc-600">{emp.goals.length}</td>
                                                <td className="px-4 py-3.5">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-14 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                                                            <div className={`h-full rounded-full ${avg >= 80 ? 'bg-emerald-500' : avg >= 50 ? 'bg-amber-500' : 'bg-red-400'}`}
                                                                style={{ width: `${avg}%` }} />
                                                        </div>
                                                        <span className="text-xs font-semibold text-zinc-600 tabular-nums">{avg}%</span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3.5">{open ? <ChevronUp className="w-4 h-4 text-zinc-400" /> : <ChevronDown className="w-4 h-4 text-zinc-400" />}</td>
                                            </tr>
                                            {open && (
                                                <tr className="bg-zinc-50/30">
                                                    <td colSpan={4} className="p-0 border-b border-zinc-100">
                                                        <div className="p-4 pl-10">
                                                            <table className="w-full text-sm mb-4">
                                                                <tbody>
                                                                    {emp.goals.map((g) => (
                                                                        <tr key={g.goal_id} className="border-b border-zinc-100/50 last:border-0">
                                                                            <td className="py-2.5 text-zinc-700">{g.goal_title}</td>
                                                                            <td className="py-2.5 text-xs text-zinc-500 w-24">T: {g.target_value || '-'}</td>
                                                                            <td className="py-2.5 text-xs text-zinc-500 w-24">A: {g.actual_value || '-'}</td>
                                                                            <td className="py-2.5 text-xs font-medium text-zinc-700 w-16">{g.computed_score !== null ? `${Math.round(g.computed_score * 100)}%` : '-'}</td>
                                                                        </tr>
                                                                    ))}
                                                                </tbody>
                                                            </table>
                                                            {emp.goals.length > 0 && (
                                                                <div className="flex gap-2 max-w-lg">
                                                                    <input
                                                                        className="flex-1 px-3 py-2 bg-white border border-zinc-200 rounded-lg text-sm placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all"
                                                                        placeholder="Add feedback for this quarter..."
                                                                        value={commentText}
                                                                        onChange={e => setCommentText(e.target.value)}
                                                                        onKeyDown={async e => {
                                                                            if (e.key === 'Enter' && commentText.trim() && !submittingComment) {
                                                                                setSubmittingComment(true);
                                                                                try {
                                                                                    await checkinsApi.addComment(emp.goals[0].sheet_id, quarter, commentText.trim());
                                                                                    toast.success('Feedback sent');
                                                                                    setCommentText('');
                                                                                } catch { toast.error('Failed to send'); }
                                                                                finally { setSubmittingComment(false); }
                                                                            }
                                                                        }}
                                                                    />
                                                                    <button
                                                                        disabled={!commentText.trim() || submittingComment}
                                                                        onClick={async () => {
                                                                            setSubmittingComment(true);
                                                                            try {
                                                                                await checkinsApi.addComment(emp.goals[0].sheet_id, quarter, commentText.trim());
                                                                                toast.success('Feedback sent');
                                                                                setCommentText('');
                                                                            } catch { toast.error('Failed to send'); }
                                                                            finally { setSubmittingComment(false); }
                                                                        }}
                                                                        className="px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 disabled:opacity-50 disabled:pointer-events-none transition-colors">
                                                                        Send
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </Fragment>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
        </div>
    );
}
