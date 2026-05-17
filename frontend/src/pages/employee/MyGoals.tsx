import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { goalsApi } from '@/api/goals';
import { adminApi } from '@/api/admin';
import { GoalCard } from '@/components/goals/GoalCard';
import { GoalForm, type GoalFormData } from '@/components/goals/GoalForm';
import { WeightageBar } from '@/components/goals/WeightageBar';
import { StatusChip } from '@/components/shared/StatusChip';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Plus, Send, AlertTriangle, Lock } from 'lucide-react';
import type { GoalSheet, Goal, Cycle } from '@/types';
import toast from 'react-hot-toast';

export default function MyGoals() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [deleteGoalId, setDeleteGoalId] = useState<string | null>(null);

  const { data: cyclesData = [], isLoading: loadingCycles } = useQuery({
    queryKey: ['cycles'],
    queryFn: () => adminApi.getCycles().catch(() => []),
    staleTime: 1000 * 60 * 5,
  });

  const activeCycle = cyclesData.find((c: Cycle) => c.is_active);

  const { data: sheet, isLoading: loadingSheet } = useQuery({
    queryKey: ['mySheet', activeCycle?.id],
    queryFn: () => activeCycle ? goalsApi.getMySheet(activeCycle.id) : null,
    enabled: !!activeCycle,
    staleTime: 1000 * 60 * 5,
  });

  const loading = loadingCycles || loadingSheet;

  const handleCreate = async (data: GoalFormData) => {
    if (!sheet) return;
    try {
      await goalsApi.createGoal({
        goal_sheet_id: sheet.id, thrust_area: data.thrust_area,
        title: data.title, description: data.description,
        uom_type: data.uom_type, target_value: data.target_value || undefined,
        target_date: data.target_date || undefined, weightage: data.weightage,
      });
      toast.success('Goal created');
      setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ['mySheet'] });
    } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const handleUpdate = async (data: GoalFormData) => {
    if (!editingGoal) return;
    try {
      await goalsApi.updateGoal(editingGoal.id, {
        thrust_area: data.thrust_area, title: data.title, description: data.description,
        uom_type: data.uom_type as 'min' | 'max' | 'timeline' | 'zero',
        target_value: data.target_value as any, target_date: data.target_date as any,
        weightage: data.weightage as any,
      });
      toast.success('Goal updated');
      setEditingGoal(null);
      queryClient.invalidateQueries({ queryKey: ['mySheet'] });
    } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const handleDelete = async () => {
    if (!deleteGoalId) return;
    try {
      await goalsApi.deleteGoal(deleteGoalId);
      toast.success('Deleted');
      setDeleteGoalId(null);
      queryClient.invalidateQueries({ queryKey: ['mySheet'] });
    } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const handleSubmit = async () => {
    if (!sheet) return;
    try {
      await goalsApi.submitSheet(sheet.id);
      toast.success('Submitted');
      setShowSubmitConfirm(false);
      queryClient.invalidateQueries({ queryKey: ['mySheet'] });
    } catch (err: any) { toast.error(err.response?.data?.message || 'Failed'); }
  };

  const total = sheet?.goals.filter(g => !g.is_shared).reduce((s, g) => s + Number(g.weightage), 0) || 0;
  const canEdit = sheet?.status === 'draft' || sheet?.status === 'returned';
  const canSubmit = total === 100 && canEdit;

  if (loading) return (
    <div className="max-w-3xl mx-auto space-y-4">
      {[1,2,3].map(i => <div key={i} className="bg-zinc-100 rounded-xl h-28 animate-pulse" />)}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-zinc-900">My Goals</h1>
          {activeCycle && <p className="text-sm text-zinc-400 mt-0.5">{activeCycle.name}</p>}
        </div>
        {sheet && <StatusChip status={sheet.status} />}
      </div>

      {/* Alerts */}
      {sheet?.status === 'returned' && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>Sheet returned for rework. Review manager feedback and update your goals.</span>
        </div>
      )}

      {sheet?.is_locked && (
        <div className="flex items-center gap-3 p-4 bg-zinc-50 border border-zinc-200 rounded-xl text-sm text-zinc-600">
          <Lock className="w-4 h-4" />
          <span>Sheet is locked. Contact admin to unlock.</span>
        </div>
      )}

      {/* Weightage */}
      {sheet && <WeightageBar used={total} />}

      {/* Goals */}
      <div className="space-y-3">
        {sheet?.goals.map((goal) => (
          <GoalCard key={goal.id} goal={goal} isLocked={!canEdit}
            onEdit={canEdit ? () => setEditingGoal(goal) : undefined}
            onDelete={canEdit ? () => setDeleteGoalId(goal.id) : undefined} />
        ))}
      </div>

      {/* Empty state */}
      {sheet && sheet.goals.length === 0 && (
        <div className="text-center py-16">
          <p className="text-zinc-400 mb-4">No goals yet</p>
          <button onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
            <Plus className="w-4 h-4" /> Add Goal
          </button>
        </div>
      )}

      {/* Actions */}
      {sheet && sheet.goals.length > 0 && canEdit && (
        <div className="flex items-center justify-between pt-4 border-t border-zinc-200">
          {sheet.goals.length < 8 && (
            <button onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
              <Plus className="w-3.5 h-3.5" /> Add Goal
            </button>
          )}
          <div className="flex items-center gap-3 ml-auto">
            {!canSubmit && <span className="text-xs text-zinc-400">Weightage must equal 100%</span>}
            <button onClick={() => setShowSubmitConfirm(true)} disabled={!canSubmit}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-40 disabled:pointer-events-none">
              <Send className="w-3.5 h-3.5" /> Submit
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <GoalForm open={showForm} onClose={() => setShowForm(false)} onSubmit={handleCreate} existingWeightage={total} />
      {editingGoal && (
        <GoalForm open onClose={() => setEditingGoal(null)} onSubmit={handleUpdate} existingWeightage={total}
          initialData={{ thrust_area: editingGoal.thrust_area, title: editingGoal.title,
            description: editingGoal.description || '', uom_type: editingGoal.uom_type,
            target_value: editingGoal.target_value, target_date: editingGoal.target_date,
            weightage: Number(editingGoal.weightage) }}
          isShared={editingGoal.is_shared} />
      )}
      <ConfirmDialog open={showSubmitConfirm} title="Submit Goal Sheet"
        message="Submit for manager approval? You won't be able to edit after submission."
        confirmText="Submit" onConfirm={handleSubmit} onCancel={() => setShowSubmitConfirm(false)} />
      <ConfirmDialog open={!!deleteGoalId} title="Delete Goal" message="Delete this goal?"
        variant="danger" confirmText="Delete" onConfirm={handleDelete} onCancel={() => setDeleteGoalId(null)} />
    </div>
  );
}
