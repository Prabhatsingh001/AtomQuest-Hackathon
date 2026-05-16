interface WeightageBarProps {
  used: number;
  total?: number;
}

export function WeightageBar({ used, total = 100 }: WeightageBarProps) {
  const pct = Math.min((used / total) * 100, 100);
  const remaining = total - used;
  const over = used > total;

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-4">
      <div className="flex justify-between text-sm mb-2">
        <span className="text-zinc-600 font-medium">{used}% allocated</span>
        {over ? (
          <span className="text-red-600 font-semibold">Exceeds 100%</span>
        ) : used === total ? (
          <span className="text-emerald-600 font-semibold">Complete</span>
        ) : (
          <span className="text-zinc-400">{remaining}% remaining</span>
        )}
      </div>
      <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            over ? 'bg-red-500' : used === total ? 'bg-emerald-500' : 'bg-zinc-900'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
