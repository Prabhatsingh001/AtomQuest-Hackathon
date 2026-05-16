import { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import type { User, Goal } from '@/types';
import { Share2, Users, Edit2, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { THRUST_AREAS } from '@/lib/utils';

const inputCls = "w-full px-3 py-2 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

export default function SharedGoals() {
  const [users, setUsers] = useState<User[]>([]);
  const [sharedGoals, setSharedGoals] = useState<Goal[]>([]);
  const [selectedEmployees, setSelectedEmployees] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<any>({});
  
  const fetchSharedGoals = () => {
    adminApi.getSharedGoals().then(setSharedGoals).catch(() => {});
  };

  const [form, setForm] = useState({
    thrust_area: THRUST_AREAS[0] || 'Business Planning', title: '', description: '', uom_type: 'min',
    target_value: 100, target_date: '', weightage: 10
  });

  useEffect(() => {
    adminApi.getUsers().then(u => setUsers(u.filter(x => x.role === 'employee'))).catch(() => toast.error('Failed to load users'));
    fetchSharedGoals();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedEmployees.length === 0) return toast.error('Select at least one employee');
    
    setLoading(true);
    const payload = {
      ...form,
      target_date: form.target_date || undefined,
      target_value: form.uom_type === 'timeline' ? undefined : form.target_value,
    };
    try {
      const res = await adminApi.pushSharedGoals(payload, selectedEmployees);
      toast.success(res.message || 'Shared goal pushed successfully');
      setForm({ ...form, title: '', description: '' });
      setSelectedEmployees([]);
      fetchSharedGoals();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        toast.error('Validation Error: ' + detail.map(d => d.msg).join(', '));
      } else {
        toast.error(detail || 'Failed to push shared goal');
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleEmp = (id: string) => {
    setSelectedEmployees(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-zinc-900">Push Shared Goals</h1>
      <p className="text-sm text-zinc-500 max-w-2xl">
        Create a top-down goal and automatically add it to the active goal sheet of multiple employees simultaneously. 
        The goals will be marked as "Shared" and linked to a parent goal on your sheet.
      </p>

      <div className="flex gap-6 mt-8">
        <div className="w-80 shrink-0 bg-white border border-zinc-200 rounded-xl p-5 self-start">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-zinc-900 flex items-center gap-2"><Users className="w-4 h-4 text-zinc-400" /> Target Audience</h2>
            <span className="text-xs font-medium bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded-full">{selectedEmployees.length} selected</span>
          </div>
          
          <div className="space-y-1 max-h-125 overflow-y-auto pr-1">
            <label className="flex items-center gap-3 p-2 hover:bg-zinc-50 rounded-lg cursor-pointer border border-transparent transition-colors mb-2">
              <input type="checkbox" className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900" 
                checked={selectedEmployees.length === users.length && users.length > 0} 
                onChange={e => setSelectedEmployees(e.target.checked ? users.map(u => u.id) : [])} />
              <span className="text-sm font-medium text-zinc-900">Select All</span>
            </label>
            <div className="h-px bg-zinc-100 my-2" />
            
            {users.map(u => (
              <label key={u.id} className="flex items-center gap-3 p-2 hover:bg-zinc-50 rounded-lg cursor-pointer border border-transparent transition-colors">
                <input type="checkbox" className="rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900"
                  checked={selectedEmployees.includes(u.id)} onChange={() => toggleEmp(u.id)} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-900 truncate">{u.full_name}</p>
                  <p className="text-xs text-zinc-500 truncate">{u.department_name || 'No department'}</p>
                </div>
              </label>
            ))}
            {users.length === 0 && <p className="text-center text-sm text-zinc-400 py-4">No employees found</p>}
          </div>
        </div>

        <div className="flex-1 min-w-0 bg-white border border-zinc-200 rounded-xl p-6 self-start">
          <h2 className="font-semibold text-zinc-900 mb-5">Goal Definition</h2>
          <form onSubmit={handleSubmit} className="space-y-4 max-w-xl">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Thrust Area</label>
                <select className={inputCls} value={form.thrust_area} onChange={e => setForm({...form, thrust_area: e.target.value})}>
                  {THRUST_AREAS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">UoM Type</label>
                <select className={inputCls} value={form.uom_type} onChange={e => setForm({...form, uom_type: e.target.value})}>
                  <option value="min">Higher is Better</option>
                  <option value="max">Lower is Better</option>
                  <option value="timeline">Timeline</option>
                  <option value="zero">Zero</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Goal Title</label>
              <input required className={inputCls} placeholder="e.g. Complete Q3 Compliance Training" value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Description</label>
              <textarea className={`${inputCls} resize-none h-24`} placeholder="Details about this shared goal..." value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Target Value</label>
                <input required type="number" step="0.01" className={inputCls} value={form.target_value} onChange={e => setForm({...form, target_value: Number(e.target.value)})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Target Date</label>
                <input required type="date" className={inputCls} value={form.target_date} onChange={e => setForm({...form, target_date: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Weightage (%)</label>
                <input required type="number" min={1} max={100} className={inputCls} value={form.weightage} onChange={e => setForm({...form, weightage: Number(e.target.value)})} />
              </div>
            </div>

            <div className="pt-4 border-t border-zinc-100">
              <button type="submit" disabled={loading || selectedEmployees.length === 0}
                className="w-full inline-flex justify-center items-center gap-2 py-2.5 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-50 disabled:pointer-events-none">
                {loading ? 'Pushing...' : <><Share2 className="w-4 h-4" /> Push to {selectedEmployees.length} Employees</>}
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="mt-12 bg-white border border-zinc-200 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-zinc-200">
          <h2 className="font-semibold text-zinc-900">Manage Shared Goals</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-200 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              <th className="px-6 py-3">Goal Details</th>
              <th className="px-6 py-3 w-32">Target</th>
              <th className="px-6 py-3 w-32">Weightage</th>
              <th className="px-6 py-3 w-24">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sharedGoals.length === 0 ? (
              <tr><td colSpan={4} className="px-6 py-8 text-center text-zinc-400">No shared goals created yet</td></tr>
            ) : sharedGoals.map(goal => {
              const isEditing = editingId === goal.id;
              return (
                <tr key={goal.id} className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50/50">
                  <td className="px-6 py-4">
                    {isEditing ? (
                      <div className="space-y-2">
                        <input className={inputCls} value={editForm.title} onChange={e => setEditForm({...editForm, title: e.target.value})} placeholder="Title" />
                        <textarea className={`${inputCls} h-16 resize-none`} value={editForm.description} onChange={e => setEditForm({...editForm, description: e.target.value})} placeholder="Description" />
                      </div>
                    ) : (
                      <>
                        <p className="font-medium text-zinc-900">{goal.title}</p>
                        <p className="text-xs text-zinc-500 mt-1">{goal.description}</p>
                        <span className="inline-block px-2 py-0.5 mt-2 bg-zinc-100 text-zinc-600 rounded text-xs">{goal.thrust_area}</span>
                      </>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {isEditing ? (
                      <input type="number" className={inputCls} value={editForm.target_value} onChange={e => setEditForm({...editForm, target_value: Number(e.target.value)})} />
                    ) : (
                      <span className="text-zinc-700">{goal.target_value !== null ? goal.target_value : '-'} {goal.uom_type !== 'zero' ? goal.uom_type : ''}</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {isEditing ? (
                      <input type="number" className={inputCls} value={editForm.weightage} onChange={e => setEditForm({...editForm, weightage: Number(e.target.value)})} />
                    ) : (
                      <span className="text-zinc-700">{goal.weightage}%</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {isEditing ? (
                      <div className="flex items-center gap-2">
                        <button onClick={async () => {
                          try {
                            await adminApi.updateSharedGoal(goal.id, editForm);
                            toast.success('Shared goal updated across all employees');
                            setEditingId(null);
                            fetchSharedGoals();
                          } catch { toast.error('Failed to update'); }
                        }} className="p-1.5 bg-zinc-900 text-white rounded hover:bg-zinc-800"><Check className="w-4 h-4" /></button>
                        <button onClick={() => setEditingId(null)} className="p-1.5 bg-zinc-100 text-zinc-600 rounded hover:bg-zinc-200"><X className="w-4 h-4" /></button>
                      </div>
                    ) : (
                      <button onClick={() => {
                        setEditingId(goal.id);
                        setEditForm({ title: goal.title, description: goal.description || '', target_value: goal.target_value || 0, weightage: goal.weightage });
                      }} className="p-1.5 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded transition-colors"><Edit2 className="w-4 h-4" /></button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
