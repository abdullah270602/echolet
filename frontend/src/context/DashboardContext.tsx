import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface UsageData {
  usedSeconds: number;
  limitSeconds: number;
  remainingSeconds: number;
}

interface DashboardContextType {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  usageData: UsageData | null;
  setUsageData: (data: UsageData) => void;
  isLoadingUsage: boolean;
  setIsLoadingUsage: (loading: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

interface DashboardProviderProps {
  children: ReactNode;
}

export function DashboardProvider({ children }: DashboardProviderProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  return (
    <DashboardContext.Provider
      value={{
        sidebarOpen,
        toggleSidebar,
        closeSidebar,
        usageData,
        setUsageData,
        isLoadingUsage,
        setIsLoadingUsage,
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
}
