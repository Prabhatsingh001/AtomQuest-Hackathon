import { useMemo } from 'react';
import type { Goal } from '@/types';

export function useWeightage(goals: Goal[]) {
  const used = useMemo(() => {
    return goals.filter(g => !g.is_shared).reduce((sum, g) => sum + Number(g.weightage), 0);
  }, [goals]);

  const remaining = 100 - used;
  const isValid = used === 100;
  const isOverflow = used > 100;

  return { used, remaining, isValid, isOverflow, total: 100 };
}
