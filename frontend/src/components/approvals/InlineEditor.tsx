import { useState } from 'react';
import type { Goal } from '@/types';

interface InlineEditorProps {
  goal: Goal;
  onSave: (goalId: string, updates: { target_value?: number; weightage?: number }) => void;
}

export function InlineEditor({ goal, onSave }: InlineEditorProps) {
  const [targetValue, setTargetValue] = useState(Number(goal.target_value) || 0);
  const [weightage, setWeightage] = useState(Number(goal.weightage));
  const [editing, setEditing] = useState(false);

  const inputCls = "px-2.5 py-1.5 border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

  if (!editing) {
    return (
      <button onClick={() => setEditing(true)} className="text-xs text-zinc-500 hover:text-zinc-800 hover:underline">
        Edit
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input type="number" className={`${inputCls} w-20`} value={targetValue}
        onChange={(e) => setTargetValue(Number(e.target.value))} />
      <input type="number" className={`${inputCls} w-16`} value={weightage}
        onChange={(e) => setWeightage(Number(e.target.value))} />
      <button
        onClick={() => { onSave(goal.id, { target_value: targetValue, weightage }); setEditing(false); }}
        className="text-xs font-medium text-emerald-600 hover:text-emerald-700">Save</button>
      <button onClick={() => setEditing(false)} className="text-xs text-zinc-400 hover:text-zinc-600">Cancel</button>
    </div>
  );
}
