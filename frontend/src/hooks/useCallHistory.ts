/**
 * useCallHistory Hook
 * Custom hook for managing call history data and state
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@clerk/clerk-react';
import type { CallHistoryItem } from '../types/callHistory';
import { fetchCallHistory, ApiError } from '../services/callHistoryApi';

interface UseCallHistoryReturn {
  calls: CallHistoryItem[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  selectedCall: CallHistoryItem | null;
  setSelectedCall: (call: CallHistoryItem | null) => void;
  isModalOpen: boolean;
  openModal: (call: CallHistoryItem) => void;
  closeModal: () => void;
}

export function useCallHistory(): UseCallHistoryReturn {
  const { getToken } = useAuth();
  const [calls, setCalls] = useState<CallHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCall, setSelectedCall] = useState<CallHistoryItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchCallHistory(getToken);
      setCalls(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch call history');
      }
      setCalls([]);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const openModal = useCallback((call: CallHistoryItem) => {
    setSelectedCall(call);
    setIsModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    // Delay clearing selectedCall to allow modal animation to complete
    setTimeout(() => setSelectedCall(null), 200);
  }, []);

  return {
    calls,
    isLoading,
    error,
    refetch: fetchData,
    selectedCall,
    setSelectedCall,
    isModalOpen,
    openModal,
    closeModal,
  };
}
