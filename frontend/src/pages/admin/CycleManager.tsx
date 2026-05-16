import { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import { StatusChip } from '@/components/shared/StatusChip';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Plus } from 'lucide-react';
import type { Cycle } from '@/types';
import toast from 'react-hot-toast';

const inputCls = "w-full px-3 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

export default function CycleManager() {
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', goal_setting_open: '', q1_open: '', q2_open: '', q3_open: '', q4_open: '' });
  const [activateId, setActivateId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try { setCycles(await adminApi.getCycles()); } catch { toast.error('Failed'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try { 
      if (editingId) {
        await adminApi.updateCycle(editingId, form as any);
        toast.success('Updated');
      } else {
        await adminApi.createCycle(form as any); 
        toast.success('Created');
      }
      setShowForm(false); 
      setEditingId(null);
      load(); 
    }
    catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const openEdit = (c: Cycle) => {
    setForm({
      name: c.name,
      goal_setting_open: c.goal_setting_open,
      q1_open: c.q1_open,
      q2_open: c.q2_open,
      q3_open: c.q3_open,
      q4_open: c.q4_open
    });
    setEditingId(c.id);
    setShowForm(true);
  };

  const handleActivate = async () => {
    if (!activateId) return;
    try { await adminApi.activateCycle(activateId); toast.success('Activated'); setActivateId(null); load(); }
    catch { toast.error('Failed'); }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-zinc-900">Cycles</h1>
        <button onClick={() => {
            setForm({ name: '', goal_setting_open: '', q1_open: '', q2_open: '', q3_open: '', q4_open: '' });
            setEditingId(null);
            setShowForm(!showForm);
          }}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
          <Plus className="w-3.5 h-3.5" /> New Cycle
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSave} className="bg-white border border-zinc-200 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Name</label>
            <input className={inputCls} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            {(['goal_setting_open', 'q1_open', 'q2_open', 'q3_open', 'q4_open'] as const).map((f) => (
              <div key={f}>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5 capitalize">{f.replace(/_/g, ' ')}</label>
                <input type="date" className={inputCls} value={(form as any)[f]}
                  onChange={(e) => setForm({ ...form, [f]: e.target.value })} required />
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-zinc-100">
            <button type="button" onClick={() => { setShowForm(false); setEditingId(null); }}
              className="px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
              Cancel
            </button>
            <button type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
              {editingId ? 'Save Changes' : 'Create'}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {loading ? [1,2].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-24 animate-pulse" />) :
          cycles.map((c) => (
            <div key={c.id} className={`bg-white border rounded-xl p-5 ${c.is_active ? 'border-emerald-300' : 'border-zinc-200'}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-semibold text-zinc-900">{c.name}</span>
                  {c.is_active && <StatusChip status="approved" />}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => openEdit(c)}
                    className="px-3 py-1.5 text-xs font-medium text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors">
                    Edit
                  </button>
                  {!c.is_active && (
                    <button onClick={() => setActivateId(c.id)}
                      className="px-3 py-1.5 text-xs font-medium text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded-lg transition-colors">
                      Activate
                    </button>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-5 gap-4 text-xs">
                {[{ l: 'Goal Setting', d: c.goal_setting_open }, { l: 'Q1', d: c.q1_open }, { l: 'Q2', d: c.q2_open }, { l: 'Q3', d: c.q3_open }, { l: 'Q4', d: c.q4_open }]
                  .map((x) => (
                    <div key={x.l}>
                      <p className="text-zinc-400 mb-0.5">{x.l}</p>
                      <p className="text-zinc-700 font-medium">{new Date(x.d).toLocaleDateString()}</p>
                    </div>
                  ))}
              </div>
            </div>
          ))}
      </div>

      <ConfirmDialog open={!!activateId} title="Activate Cycle" message="This deactivates the current cycle. Continue?"
        confirmText="Activate" onConfirm={handleActivate} onCancel={() => setActivateId(null)} />
    </div>
  );
}
