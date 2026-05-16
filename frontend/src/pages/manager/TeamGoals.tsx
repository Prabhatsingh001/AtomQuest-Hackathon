import { useState, useEffect, useCallback } from 'react';
import { approvalsApi } from '@/api/approvals';
import { StatusChip } from '@/components/shared/StatusChip';
import { GoalCard } from '@/components/goals/GoalCard';
import { WeightageBar } from '@/components/goals/WeightageBar';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { InlineEditor } from '@/components/approvals/InlineEditor';
import { Check, RotateCcw, X } from 'lucide-react';
import type { GoalSheet } from '@/types';
import toast from 'react-hot-toast';

export default function TeamGoals() {
  const [queue, setQueue] = useState<GoalSheet[]>([]);
  const [selected, setSelected] = useState<GoalSheet | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReturn, setShowReturn] = useState(false);
  const [returnComment, setReturnComment] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try { setQueue(await approvalsApi.getQueue()); } catch { toast.error('Failed to load'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        const items = await approvalsApi.getQueue();
        if (!cancelled) setQueue(items);
      } catch {
        if (!cancelled) toast.error('Failed to load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleApprove = async (id: string) => {
    try { await approvalsApi.approve(id); toast.success('Approved'); setSelected(null); load(); }
    catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const handleReturn = async () => {
    if (!selected) return;
    try { await approvalsApi.returnSheet(selected.id, returnComment); toast.success('Returned'); setShowReturn(false); setReturnComment(''); setSelected(null); load(); }
    catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const handleInlineEdit = async (goalId: string, updates: { target_value?: number; weightage?: number }) => {
    if (!selected) return;
    try {
      await approvalsApi.inlineEdit(selected.id, goalId, updates);
      toast.success('Goal updated');
      // Reload selected sheet
      const updatedSheet = await approvalsApi.getSheet(selected.id);
      setSelected(updatedSheet);
      load(); // refresh queue sidebar
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Failed to update goal');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-zinc-900">Approval Queue</h1>

      <div className="flex gap-6">
        {/* Sidebar list */}
        <div className="w-64 space-y-2 shrink-0">
          {loading ? [1,2].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-20 animate-pulse" />) :
            queue.length === 0 ? (
              <p className="text-sm text-zinc-400 py-12 text-center">No pending approvals</p>
            ) : queue.map((s) => (
              <button key={s.id} onClick={() => setSelected(s)}
                className={`w-full text-left p-4 rounded-xl border text-sm transition-all ${
                  selected?.id === s.id ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-200 bg-white hover:bg-zinc-50 hover:border-zinc-300'
                }`}>
                <p className="font-semibold text-zinc-800">{s.employee_name}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <StatusChip status={s.status} />
                  <span className="text-xs text-zinc-400">{s.goals.length} goals</span>
                </div>
              </button>
            ))}
        </div>

        {/* Detail panel */}
        <div className="flex-1 min-w-0">
          {selected ? (
            <div className="bg-white border border-zinc-200 rounded-xl p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-zinc-900">{selected.employee_name}</h2>
                  <p className="text-xs text-zinc-400 mt-0.5">{selected.goals.length} goals · {Number(selected.total_weightage)}%</p>
                </div>
                <button onClick={() => setSelected(null)} className="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <WeightageBar used={Number(selected.total_weightage)} />
              <div className="space-y-3">
                {selected.goals.map((g) => (
                  <GoalCard 
                    key={g.id} 
                    goal={g} 
                    isLocked={selected.status !== 'submitted'} 
                    inlineEditNode={
                      selected.status === 'submitted' ? (
                        <InlineEditor goal={g} onSave={handleInlineEdit} />
                      ) : undefined
                    }
                  />
                ))}
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-zinc-100">
                <button onClick={() => setShowReturn(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
                  <RotateCcw className="w-3.5 h-3.5" /> Return
                </button>
                <button onClick={() => handleApprove(selected.id)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-400 py-20 text-center">Select a sheet to review</p>
          )}
        </div>
      </div>

      <ConfirmDialog open={showReturn} title="Return for Rework" message="Provide feedback for the employee."
        variant="warning" confirmText="Return" onConfirm={handleReturn}
        onCancel={() => { setShowReturn(false); setReturnComment(''); }}
        requireInput inputPlaceholder="Feedback..." onInputChange={setReturnComment} />
    </div>
  );
}
