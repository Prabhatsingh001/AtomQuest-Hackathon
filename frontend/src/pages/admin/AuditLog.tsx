import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '@/api/admin';
import { Download, Filter } from 'lucide-react';
import type { AuditLog } from '@/types';
import toast from 'react-hot-toast';

const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function AuditLogPage() {
    const [page, setPage] = useState(1);
    const [entityFilter, setEntityFilter] = useState('');

    const { data = { items: [], total: 0 }, isLoading: loading } = useQuery<{ items: AuditLog[]; total: number }>({
        queryKey: ['auditLogs', page, entityFilter],
        queryFn: () => adminApi.getAuditLogs({ page, page_size: 20, entity_type: entityFilter || undefined }),
        staleTime: 1000 * 60 * 2,
    });

    const logs: AuditLog[] = data.items;
    const total = data.total;

    const exportCsv = () => {
        const rows = [['Time', 'By', 'Entity', 'Action', 'Reason']];
        logs.forEach((l: AuditLog) => rows.push([new Date(l.timestamp).toISOString(), l.changed_by_name || '', `${l.entity_type}:${l.entity_id}`, l.action, l.reason || '']));
        const blob = new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'audit.csv'; a.click();
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-lg font-bold text-zinc-900">Audit Log</h1>
                <button onClick={exportCsv}
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
                    <Download className="w-3.5 h-3.5" /> Export
                </button>
            </div>

            <div className="flex items-center gap-3">
                <Filter className="w-4 h-4 text-zinc-400" />
                <select
                    className="px-3 py-2 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 cursor-pointer w-40"
                    value={entityFilter} onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}>
                    <option value="">All entities</option>
                    <option value="goal">Goals</option>
                    <option value="goal_sheet">Sheets</option>
                    <option value="achievement">Achievements</option>
                </select>
                <span className="text-xs text-zinc-400 font-medium">{total} entries</span>
            </div>

            {loading ? <div className="bg-zinc-100 rounded-xl h-48 animate-pulse" /> :
                logs.length === 0 ? <p className="text-center py-16 text-zinc-400 text-sm">No entries</p> : (
                    <div className="bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full shadow-sm">
                        <table className="w-full text-sm min-w-[600px]">
                            <thead><tr><th className={thCls}>Time</th><th className={thCls}>By</th><th className={thCls}>Entity</th><th className={thCls}>Action</th><th className={thCls}>Reason</th></tr></thead>
                            <tbody>
                                {logs.map((l: AuditLog) => (
                                    <tr key={l.id} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                                        <td className="px-4 py-3 text-xs text-zinc-500 whitespace-nowrap tabular-nums">{new Date(l.timestamp).toLocaleString()}</td>
                                        <td className="px-4 py-3 text-zinc-700">{l.changed_by_name || 'System'}</td>
                                        <td className="px-4 py-3">
                                            <span className="text-xs font-medium px-2 py-1 bg-zinc-100 text-zinc-600 rounded-md">{l.entity_type}</span>
                                        </td>
                                        <td className="px-4 py-3 text-zinc-700">{l.action}</td>
                                        <td className="px-4 py-3 text-zinc-500">{l.reason || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

            <div className="flex justify-center gap-2 pt-2">
                <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                    className="px-3 py-1.5 text-sm text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors disabled:opacity-30 disabled:pointer-events-none">
                    Prev
                </button>
                <span className="text-sm text-zinc-400 py-1.5 tabular-nums">Page {page}</span>
                <button disabled={logs.length < 20} onClick={() => setPage(p => p + 1)}
                    className="px-3 py-1.5 text-sm text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors disabled:opacity-30 disabled:pointer-events-none">
                    Next
                </button>
            </div>
        </div>
    );
}
