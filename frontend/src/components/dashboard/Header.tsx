import { useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';

const pageTitles: Record<string, string> = {
  '/app': 'Agent Sandbox',
  '/app/config': 'Agent Configuration',
  '/app/history': 'Call History',
  '/app/settings': 'Settings',
};

export function Header() {
  const location = useLocation();
  const { toggleSidebar } = useDashboard();

  // Get the title based on current path
  const title = pageTitles[location.pathname] || 'Dashboard';

  return (
    <header className="h-16 border-b border-rule bg-paper flex items-center px-6">
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="md:hidden p-2 -ml-2 mr-4 text-muted hover:text-ink transition-colors"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      <h1
        key={location.pathname}
        className="font-display text-xl font-bold text-ink"
      >
        {title}
      </h1>
    </header>
  );
}
