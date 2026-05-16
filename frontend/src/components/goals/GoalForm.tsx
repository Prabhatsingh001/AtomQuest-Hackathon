import { useState } from 'react';
import { THRUST_AREAS } from '@/lib/utils';
import { X } from 'lucide-react';

interface GoalFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: GoalFormData) => void;
  existingWeightage: number;
  initialData?: Partial<GoalFormData>;
  isShared?: boolean;
}

export interface GoalFormData {
  thrust_area: string;
  title: string;
  description: string;
  uom_type: string;
  target_value: number | null;
  target_date: string | null;
  weightage: number;
}

export function GoalForm({ open, onClose, onSubmit, existingWeightage, initialData, isShared }: GoalFormProps) {
  const [form, setForm] = useState<GoalFormData>({
    thrust_area: initialData?.thrust_area || '',
    title: initialData?.title || '',
    description: initialData?.description || '',
    uom_type: initialData?.uom_type || 'min',
    target_value: initialData?.target_value || null,
    target_date: initialData?.target_date || null,
    weightage: initialData?.weightage || 10,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!open) return null;

  const maxWeightage = 100 - existingWeightage + (initialData?.weightage || 0);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.thrust_area) errs.thrust_area = 'Required';
    if (!form.title) errs.title = 'Required';
    if (form.weightage < 10) errs.weightage = 'Minimum 10%';
    if (form.weightage > maxWeightage) errs.weightage = `Max available: ${maxWeightage}%`;
    if ((form.uom_type === 'min' || form.uom_type === 'max') && !form.target_value)
      errs.target_value = 'Required for this UoM';
    if (form.uom_type === 'timeline' && !form.target_date)
      errs.target_date = 'Required for timeline';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) onSubmit(form);
  };

  const inputCls = "w-full px-3 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";
  const selectCls = "w-full px-3 py-2.5 bg-white border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 cursor-pointer transition-all";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/25 backdrop-blur-[1px]" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl border border-zinc-200 p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-zinc-900">{initialData ? 'Edit Goal' : 'Add Goal'}</h3>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Thrust Area</label>
            <select className={selectCls} value={form.thrust_area} disabled={isShared}
              onChange={(e) => setForm({ ...form, thrust_area: e.target.value })}>
              <option value="">Select...</option>
              {THRUST_AREAS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            {errors.thrust_area && <p className="text-red-600 text-xs mt-1.5">{errors.thrust_area}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Title</label>
            <input className={inputCls} value={form.title} disabled={isShared}
              onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Goal title" />
            {errors.title && <p className="text-red-600 text-xs mt-1.5">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">Description</label>
            <textarea className={`${inputCls} resize-none`} rows={2} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional description" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">UoM Type</label>
              <select className={selectCls} value={form.uom_type} disabled={isShared}
                onChange={(e) => setForm({ ...form, uom_type: e.target.value })}>
                <option value="min">Higher is Better</option>
                <option value="max">Lower is Better</option>
                <option value="timeline">Timeline</option>
                <option value="zero">Zero</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Weightage (%)</label>
              <input type="number" className={inputCls} min={10} max={100} disabled={isShared}
                value={form.weightage}
                onChange={(e) => setForm({ ...form, weightage: Number(e.target.value) })} />
              {errors.weightage && <p className="text-red-600 text-xs mt-1.5">{errors.weightage}</p>}
            </div>
          </div>

          {(form.uom_type === 'min' || form.uom_type === 'max') && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Target Value</label>
              <input type="number" className={inputCls} disabled={isShared}
                value={form.target_value || ''} step="0.01"
                onChange={(e) => setForm({ ...form, target_value: Number(e.target.value) })} />
              {errors.target_value && <p className="text-red-600 text-xs mt-1.5">{errors.target_value}</p>}
            </div>
          )}

          {form.uom_type === 'timeline' && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">Target Date</label>
              <input type="date" className={inputCls} disabled={isShared}
                value={form.target_date || ''}
                onChange={(e) => setForm({ ...form, target_date: e.target.value })} />
              {errors.target_date && <p className="text-red-600 text-xs mt-1.5">{errors.target_date}</p>}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-zinc-100">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors">
              Cancel
            </button>
            <button type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors">
              {initialData ? 'Save Changes' : 'Add Goal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
