import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AudioWaveform, Mic, Settings2, History, Cog } from 'lucide-react';
import { UserButton } from '@clerk/clerk-react';
import { dark } from '@clerk/themes';
import { useUsageData, formatUsageTime, getUsagePercentage } from '../../hooks/useUsageData';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Agent Sandbox', path: '/app', icon: <Mic className="w-5 h-5" /> },
  { label: 'Agent Configuration', path: '/app/config', icon: <Settings2 className="w-5 h-5" /> },
  { label: 'Call History', path: '/app/history', icon: <History className="w-5 h-5" /> },
  { label: 'Settings', path: '/app/settings', icon: <Cog className="w-5 h-5" /> },
];

export function Sidebar() {
  const location = useLocation();
  const { usageData, isLoading } = useUsageData();

  const isActive = (path: string) => {
    if (path === '/app') {
      return location.pathname === '/app';
    }
    return location.pathname.startsWith(path);
  };

  const usagePercentage = usageData
    ? getUsagePercentage(usageData.usedSeconds, usageData.limitSeconds)
    : 0;

  return (
    <aside className="fixed left-0 top-0 h-full w-60 glass-strong border-r border-white/10 flex flex-col z-40">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <Link to="/" className="flex items-center gap-2 text-white">
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="flex items-center gap-2"
          >
            <div className="relative">
              <AudioWaveform className="w-7 h-7 text-teal-400" />
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute inset-0 bg-teal-400/20 rounded-full blur-lg"
              />
            </div>
            <span className="text-lg font-bold">Echolet</span>
          </motion.div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                ${active
                  ? 'bg-teal-500/10 text-teal-400 border-l-2 border-teal-400 -ml-[2px] pl-[14px]'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
                }
              `}
            >
              <span className={active ? 'text-teal-400' : ''}>{item.icon}</span>
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Usage Indicator */}
      <div className="p-4 border-t border-white/10">
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-white/50">Daily Limit</span>
            {isLoading ? (
              <span className="text-white/30">Loading...</span>
            ) : usageData ? (
              <span className="text-white/70">
                {formatUsageTime(usageData.usedSeconds)} / {formatUsageTime(usageData.limitSeconds)}
              </span>
            ) : null}
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${usagePercentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className={`h-full rounded-full ${
                usagePercentage > 80
                  ? 'bg-red-500'
                  : usagePercentage > 50
                  ? 'bg-amber-500'
                  : 'bg-gradient-to-r from-teal-500 to-purple-500'
              }`}
            />
          </div>
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-white/10">
        <UserButton
          appearance={{
            baseTheme: dark,
            elements: {
              avatarBox: 'w-9 h-9',
              userButtonTrigger: 'focus:shadow-none',
              userButtonPopoverCard: 'bg-midnight-800 border border-white/10',
              userButtonPopoverActionButton: 'text-white/70 hover:text-white hover:bg-white/5',
              userButtonPopoverActionButtonText: 'text-white/70',
              userButtonPopoverActionButtonIcon: 'text-white/50',
              userButtonPopoverFooter: 'hidden',
            },
          }}
        />
      </div>
    </aside>
  );
}
