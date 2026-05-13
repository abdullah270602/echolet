import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/clerk-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

interface UsageData {
  usedSeconds: number;
  limitSeconds: number;
  remainingSeconds: number;
}

interface UseUsageDataReturn {
  usageData: UsageData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useUsageData(): UseUsageDataReturn {
  const { getToken } = useAuth();
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsage = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const token = await getToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      // Fetch usage data from the backend
      const response = await fetch(`${API_BASE_URL}/livekit/usage`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch usage data');
      }

      const data = await response.json();

      setUsageData({
        usedSeconds: data.used_seconds,
        limitSeconds: data.limit_seconds,
        remainingSeconds: data.remaining_seconds,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setUsageData(null);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  return {
    usageData,
    isLoading,
    error,
    refetch: fetchUsage,
  };
}

// Helper to format seconds as "Xm Ys" or "X:YY"
export function formatUsageTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  return `${remainingSeconds}s`;
}

// Helper to format as percentage
export function getUsagePercentage(used: number, limit: number): number {
  if (limit === 0) return 100;
  return Math.min(100, Math.round((used / limit) * 100));
}
