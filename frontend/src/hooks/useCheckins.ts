import { useState, useEffect, useCallback } from 'react';
import { checkinsApi } from '@/api/checkins';
import type { CheckinGoalData } from '@/types';

export function useCheckins(cycleId: string | null, quarter: string) {
  const [checkins, setCheckins] = useState<CheckinGoalData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCheckins = useCallback(async () => {
    if (!cycleId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await checkinsApi.getMy(cycleId, quarter);
      setCheckins(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load check-ins');
    } finally {
      setLoading(false);
    }
  }, [cycleId, quarter]);

  useEffect(() => {
    fetchCheckins();
  }, [fetchCheckins]);

  return { checkins, loading, error, refetch: fetchCheckins };
}
