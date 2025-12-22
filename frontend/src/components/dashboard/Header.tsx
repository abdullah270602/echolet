import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
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
    <header className="h-16 border-b border-white/10 bg-midnight-900/50 backdrop-blur-sm flex items-center px-6">
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="md:hidden p-2 -ml-2 mr-4 text-white/60 hover:text-white transition-colors"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      <motion.h1
        key={location.pathname}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="text-lg font-semibold text-white"
      >
        {title}
      </motion.h1>
    </header>
  );
}
