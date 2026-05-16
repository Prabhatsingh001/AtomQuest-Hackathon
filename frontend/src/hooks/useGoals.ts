import { useState, useEffect, useCallback } from 'react';
import { goalsApi } from '@/api/goals';
import type { GoalSheet } from '@/types';

export function useGoals(cycleId: string | null) {
  const [sheet, setSheet] = useState<GoalSheet | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSheet = useCallback(async () => {
    if (!cycleId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await goalsApi.getMySheet(cycleId);
      setSheet(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load goals');
    } finally {
      setLoading(false);
    }
  }, [cycleId]);

  useEffect(() => {
    fetchSheet();
  }, [fetchSheet]);

  return { sheet, loading, error, refetch: fetchSheet };
}
