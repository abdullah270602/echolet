import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/clerk-react';

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
      // We'll use the token endpoint which returns remaining_seconds
      const response = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          room_name: 'usage-check',
          name: 'Usage Check',
        }),
      });

      if (response.status === 403) {
        // Daily limit reached
        setUsageData({
          usedSeconds: 60, // Default limit
          limitSeconds: 60,
          remainingSeconds: 0,
        });
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch usage data');
      }

      const data = await response.json();

      // Calculate used seconds from remaining
      const limitSeconds = 60; // Default 1 minute limit - should match backend config
      const remainingSeconds = data.remaining_seconds || 0;
      const usedSeconds = Math.max(0, limitSeconds - remainingSeconds);

      setUsageData({
        usedSeconds,
        limitSeconds,
        remainingSeconds,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      // Set default values on error
      setUsageData({
        usedSeconds: 0,
        limitSeconds: 60,
        remainingSeconds: 60,
      });
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
