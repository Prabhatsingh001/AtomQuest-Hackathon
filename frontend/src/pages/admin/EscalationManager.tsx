import { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import type { EscalationRule } from '@/types';
import { Plus, Edit2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const inputCls = "w-full px-3 py-2 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

export default function EscalationManager() {
  const [rules, setRules] = useState<EscalationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<EscalationRule | null>(null);
  const [isNew, setIsNew] = useState(false);
  
  const [form, setForm] = useState({
    name: '', trigger_event: 'goal_not_submitted', days_threshold: 3,
    notify_employee: true, notify_manager: true, notify_hr: false, is_active: true
  });

  const load = async () => {
    setLoading(true);
    try { setRules(await adminApi.getEscalationRules()); }
    catch { toast.error('Failed to load rules'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isNew) {
        await adminApi.createEscalationRule(form as any);
        toast.success('Rule created');
      } else if (editing) {
        await adminApi.updateEscalationRule(editing.id, form as any);
        toast.success('Rule updated');
      }
      setEditing(null);
      setIsNew(false);
      load();
    } catch (err: any) {
      toast.error('Operation failed');
    }
  };

  const openEdit = (r: EscalationRule) => {
    setForm({
      name: r.name, trigger_event: r.trigger_event, days_threshold: r.days_threshold,
      notify_employee: r.notify_employee, notify_manager: r.notify_manager, 
      notify_hr: r.notify_hr, is_active: r.is_active
    });
    setEditing(r);
    setIsNew(false);
  };

  const openNew = () => {
    setForm({
      name: '', trigger_event: 'goal_not_submitted', days_threshold: 3,
      notify_employee: true, notify_manager: true, notify_hr: false, is_active: true
    });
    setIsNew(true);
    setEditing(null);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-zinc-900">Escalation Rules</h1>
        <button onClick={openNew}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
          <Plus className="w-4 h-4" /> Add Rule
        </button>
      </div>

      <div className="flex gap-6">
        <div className="flex-1 min-w-0 bg-white border border-zinc-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead>
              <tr>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Name</th>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Trigger Event</th>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Threshold</th>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Notifications</th>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs">Status</th>
                <th className="px-4 py-3 font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-50 border-b border-zinc-200 text-xs w-10"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? <tr><td colSpan={6} className="p-8 text-center text-zinc-400">Loading...</td></tr> :
               rules.length === 0 ? <tr><td colSpan={6} className="p-8 text-center text-zinc-400">No rules configured.</td></tr> :
               rules.map(r => (
                <tr key={r.id} className="border-b border-zinc-100 last:border-b-0 hover:bg-zinc-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-zinc-800 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-zinc-400" /> {r.name}
                  </td>
                  <td className="px-4 py-3 text-zinc-600 capitalize">{(r.trigger_event || '').replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-zinc-600">{r.days_threshold} days</td>
                  <td className="px-4 py-3 text-zinc-600 text-xs">
                    {[
                      r.notify_employee && 'Employee',
                      r.notify_manager && 'Manager',
                      r.notify_hr && 'HR'
                    ].filter(Boolean).join(', ')}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${r.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-zinc-100 text-zinc-600'}`}>
                      {r.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => openEdit(r)} className="p-1.5 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-200 rounded-md transition-colors">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(isNew || editing) && (
          <div className="w-80 flex-shrink-0 bg-white border border-zinc-200 rounded-xl p-5 self-start sticky top-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-semibold text-zinc-900">{isNew ? 'New Rule' : 'Edit Rule'}</h2>
              <button onClick={() => { setIsNew(false); setEditing(null); }} className="text-zinc-400 hover:text-zinc-600 text-sm">Cancel</button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">Rule Name</label>
                <input required className={inputCls} value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">Trigger Event</label>
                <select className={inputCls} value={form.trigger_event} onChange={e => setForm({...form, trigger_event: e.target.value})}>
                  <option value="goal_not_submitted">Goal Not Submitted</option>
                  <option value="goal_not_approved">Goal Not Approved</option>
                  <option value="checkin_not_done">Check-in Not Done</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">Threshold (Days)</label>
                <input required type="number" min={1} className={inputCls} value={form.days_threshold} onChange={e => setForm({...form, days_threshold: Number(e.target.value)})} />
              </div>
              
              <div className="space-y-2 pt-2 border-t border-zinc-100">
                <label className="block text-xs font-medium text-zinc-700">Notifications</label>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="notify-emp" checked={form.notify_employee} onChange={e => setForm({...form, notify_employee: e.target.checked})} className="rounded border-zinc-300 text-zinc-900" />
                  <label htmlFor="notify-emp" className="text-sm text-zinc-700">Notify Employee</label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="notify-mgr" checked={form.notify_manager} onChange={e => setForm({...form, notify_manager: e.target.checked})} className="rounded border-zinc-300 text-zinc-900" />
                  <label htmlFor="notify-mgr" className="text-sm text-zinc-700">Notify Manager</label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="notify-hr" checked={form.notify_hr} onChange={e => setForm({...form, notify_hr: e.target.checked})} className="rounded border-zinc-300 text-zinc-900" />
                  <label htmlFor="notify-hr" className="text-sm text-zinc-700">Notify HR (Admin)</label>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <input type="checkbox" id="active-check" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900" />
                <label htmlFor="active-check" className="text-sm text-zinc-700">Rule is active</label>
              </div>
              <button type="submit" className="w-full py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors mt-2">
                {isNew ? 'Create Rule' : 'Save Changes'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
