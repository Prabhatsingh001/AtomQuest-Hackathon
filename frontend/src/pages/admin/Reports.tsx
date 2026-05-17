import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '@/api/reports';
import { Download } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import toast from 'react-hot-toast';

const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function Reports() {
    const [tab, setTab] = useState<'report' | 'trends' | 'distribution'>('report');

    const { data: report = [], isLoading: l1 } = useQuery<any[]>({
        queryKey: ['achievementReport'],
        queryFn: () => reportsApi.getAchievementReport(),
        staleTime: 1000 * 60 * 2,
    });

    const { data: qoq = [], isLoading: l2 } = useQuery<any[]>({
        queryKey: ['qoqTrends'],
        queryFn: () => reportsApi.getQoQTrends(),
        staleTime: 1000 * 60 * 2,
    });

    const { data: distribution = { by_thrust_area: [], by_uom_type: [] }, isLoading: l3 } = useQuery<any>({
        queryKey: ['distribution'],
        queryFn: () => reportsApi.getDistribution(),
        staleTime: 1000 * 60 * 2,
    });

    const loading = l1 || l2 || l3;

    const handleExport = async (type: 'csv' | 'excel') => {
        try {
            const blob = type === 'csv' ? await reportsApi.exportCsv() : await reportsApi.exportExcel();
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
            a.download = `report.${type === 'csv' ? 'csv' : 'xlsx'}`; a.click();
        } catch { toast.error('Export failed'); }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-lg font-bold text-zinc-900">Reports</h1>
                <div className="flex gap-2">
                    <button onClick={() => handleExport('csv')}
                        className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
                        <Download className="w-3.5 h-3.5" /> CSV
                    </button>
                    <button onClick={() => handleExport('excel')}
                        className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
                        <Download className="w-3.5 h-3.5" /> Excel
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-zinc-200 overflow-x-auto pb-1">
                {[{ k: 'report', l: 'Achievement' }, { k: 'trends', l: 'QoQ Trends' }, { k: 'distribution', l: 'Distribution' }].map((t) => (
                    <button key={t.k} onClick={() => setTab(t.k as any)}
                        className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors shrink-0 ${tab === t.k ? 'border-zinc-900 text-zinc-900 font-semibold' : 'border-transparent text-zinc-400 hover:text-zinc-600'
                            }`}>{t.l}</button>
                ))}
            </div>

            {loading ? <div className="bg-zinc-100 rounded-xl h-48 animate-pulse" /> : (
                <>
                    {tab === 'report' && (
                        <div className="bg-white border border-zinc-200 rounded-xl overflow-x-auto max-w-full shadow-sm">
                            <table className="w-full text-sm min-w-[800px]">
                                <thead><tr>
                                    {['Employee', 'Dept', 'Goal', 'UoM', 'Target', 'Q1', 'Q2', 'Q3', 'Q4'].map(h => <th key={h} className={thCls}>{h}</th>)}
                                </tr></thead>
                                <tbody>
                                    {report.map((r: any, i: number) => (
                                        <tr key={i} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                                            <td className="px-4 py-3 font-medium text-zinc-800 whitespace-nowrap">{r.employee_name}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.department || '-'}</td>
                                            <td className="px-4 py-3 text-zinc-700 max-w-xs truncate">{r.goal_title}</td>
                                            <td className="px-4 py-3 text-xs text-zinc-500">{r.uom_type}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.target}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.q1_actual || '-'}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.q2_actual || '-'}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.q3_actual || '-'}</td>
                                            <td className="px-4 py-3 text-zinc-600">{r.q4_actual || '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {report.length === 0 && <p className="text-center py-12 text-zinc-400 text-sm">No data</p>}
                        </div>
                    )}

                    {tab === 'trends' && (
                        <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={qoq.map((q: any) => ({ ...q, score: Math.round(q.avg_score * 100) }))}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                                    <XAxis dataKey="quarter" stroke="#a1a1aa" fontSize={12} />
                                    <YAxis stroke="#a1a1aa" fontSize={12} />
                                    <Tooltip contentStyle={{ border: '1px solid #e4e4e7', borderRadius: '8px', fontSize: '13px' }} />
                                    <Line type="monotone" dataKey="score" stroke="#18181b" strokeWidth={2} dot={{ fill: '#18181b', r: 4 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {tab === 'distribution' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
                                <p className="text-sm font-semibold text-zinc-900 mb-4">By Thrust Area</p>
                                <ResponsiveContainer width="100%" height={240}>
                                    <BarChart data={distribution.by_thrust_area}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                                        <XAxis dataKey="name" stroke="#a1a1aa" fontSize={10} />
                                        <YAxis stroke="#a1a1aa" fontSize={12} />
                                        <Tooltip contentStyle={{ border: '1px solid #e4e4e7', borderRadius: '8px', fontSize: '13px' }} />
                                        <Bar dataKey="count" fill="#3f3f46" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
                                <p className="text-sm font-semibold text-zinc-900 mb-4">By UoM Type</p>
                                <ResponsiveContainer width="100%" height={240}>
                                    <BarChart data={distribution.by_uom_type}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                                        <XAxis dataKey="name" stroke="#a1a1aa" fontSize={10} />
                                        <YAxis stroke="#a1a1aa" fontSize={12} />
                                        <Tooltip contentStyle={{ border: '1px solid #e4e4e7', borderRadius: '8px', fontSize: '13px' }} />
                                        <Bar dataKey="count" fill="#71717a" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
