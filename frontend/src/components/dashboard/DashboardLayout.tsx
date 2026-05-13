import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { DashboardProvider, useDashboard } from '../../context/DashboardContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

function DashboardContent() {
  const { sidebarOpen, closeSidebar } = useDashboard();

  return (
    <div className="landing min-h-screen bg-paper font-body text-ink">
      {/* Desktop Sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-ink/40 z-40 md:hidden"
              onClick={closeSidebar}
            />

            {/* Mobile Sidebar */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 h-full w-60 z-50 md:hidden"
            >
              <Sidebar />
              {/* Close button */}
              <button
                onClick={closeSidebar}
                className="absolute top-4 right-4 p-2 text-muted hover:text-ink transition-colors"
                aria-label="Close sidebar"
              >
                <X className="w-5 h-5" />
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="md:ml-60 min-h-screen flex flex-col">
        <Header />

        {/* Page Content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function DashboardLayout() {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
}
