import { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import toast from 'react-hot-toast';

const thCls = "px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200";

export default function OrgDashboard() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getCompletionDashboard().then(setData).catch(() => toast.error('Failed')).finally(() => setLoading(false));
  }, []);

  const total = data.reduce((s, d) => s + d.total_employees, 0);
  const avgGoal = data.length ? Math.round(data.reduce((s, d) => s + d.goal_setting_done_pct, 0) / data.length) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-zinc-900">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Employees', value: total },
          { label: 'Goal Setting', value: `${avgGoal}%` },
          { label: 'Departments', value: data.length },
        ].map((stat) => (
          <div key={stat.label} className="bg-white border border-zinc-200 rounded-xl p-5">
            <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">{stat.label}</p>
            <p className="text-2xl font-bold text-zinc-900 mt-1.5">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      {loading ? <div className="bg-zinc-100 rounded-xl h-48 animate-pulse" /> : (
        <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className={thCls}>Department</th>
                <th className={thCls}>Employees</th>
                <th className={thCls}>Goal Setting</th>
                <th className={thCls}>Q1</th>
                <th className={thCls}>Q2</th>
                <th className={thCls}>Q3</th>
                <th className={thCls}>Q4</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50/60 transition-colors">
                  <td className="px-4 py-3 font-medium text-zinc-800">{row.department}</td>
                  <td className="px-4 py-3 text-zinc-600">{row.total_employees}</td>
                  {[row.goal_setting_done_pct, row.q1_done_pct, row.q2_done_pct, row.q3_done_pct, row.q4_done_pct].map((p, j) => (
                    <td key={j} className="px-4 py-3">
                      <span className={`text-xs font-semibold ${p >= 80 ? 'text-emerald-600' : p >= 50 ? 'text-amber-600' : 'text-red-500'}`}>
                        {p.toFixed(0)}%
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
