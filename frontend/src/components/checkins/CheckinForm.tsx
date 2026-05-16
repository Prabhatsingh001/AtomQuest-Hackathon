import { useState } from 'react';

interface CheckinFormProps {
  onSubmit: (actual: number, status: string) => void;
  initialActual?: number;
  initialStatus?: string;
  uomType: string;
}

export function CheckinForm({ onSubmit, initialActual, initialStatus, uomType }: CheckinFormProps) {
  const [actual, setActual] = useState(initialActual || 0);
  const [status, setStatus] = useState(initialStatus || 'not_started');

  const inputCls = "px-2.5 py-1.5 border border-zinc-200 rounded-lg text-sm text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all";

  return (
    <div className="flex items-center gap-2">
      {uomType !== 'timeline' && (
        <input type="number" className={`${inputCls} w-24`} value={actual}
          onChange={(e) => setActual(Number(e.target.value))}
          onBlur={() => onSubmit(actual, status)} step="0.01" />
      )}
      <select className={`${inputCls} w-32 cursor-pointer`} value={status}
        onChange={(e) => { setStatus(e.target.value); onSubmit(actual, e.target.value); }}>
        <option value="not_started">Not Started</option>
        <option value="on_track">On Track</option>
        <option value="completed">Completed</option>
      </select>
    </div>
  );
}
