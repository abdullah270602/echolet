import { Link, useLocation } from 'react-router-dom';
import { Mic, Settings2, History, Cog } from 'lucide-react';
import { UserButton } from '@clerk/clerk-react';
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
    <aside className="fixed left-0 top-0 h-full w-60 bg-white border-r border-rule flex flex-col z-40">
      {/* Logo */}
      <div className="h-16 px-6 border-b border-rule flex items-center">
        <Link to="/" className="font-display text-xl font-bold text-ink">
          Echolet
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
                flex items-center gap-3 px-3 py-2.5 transition-colors
                ${active
                  ? 'bg-paper text-ink font-semibold border-l-2 border-accent -ml-[2px] pl-[14px]'
                  : 'text-muted hover:text-ink hover:bg-paper/60'
                }
              `}
            >
              <span className={active ? 'text-accent' : ''}>{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Usage Indicator */}
      <div className="p-4 border-t border-rule">
        <div className="mb-1">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-muted">Daily Limit</span>
            {isLoading ? (
              <span className="text-muted">Loading...</span>
            ) : usageData ? (
              <span className="text-ink font-medium tabular-nums">
                {formatUsageTime(usageData.usedSeconds)} / {formatUsageTime(usageData.limitSeconds)}
              </span>
            ) : null}
          </div>
          <div className="h-2 bg-paper border border-rule overflow-hidden">
            <div
              style={{ width: `${usagePercentage}%` }}
              className={`h-full transition-all duration-300 ${
                usagePercentage > 80
                  ? 'bg-red-600'
                  : usagePercentage > 50
                  ? 'bg-amber-600'
                  : 'bg-accent'
              }`}
            />
          </div>
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-rule">
        <UserButton
          appearance={{
            elements: {
              avatarBox: 'w-9 h-9',
              userButtonTrigger: 'focus:shadow-none',
              userButtonPopoverCard: 'bg-white border-2 border-ink rounded-none shadow-none',
              userButtonPopoverActionButton: 'text-ink hover:bg-paper',
              userButtonPopoverActionButtonText: 'text-ink',
              userButtonPopoverActionButtonIcon: 'text-muted',
              userButtonPopoverFooter: 'hidden',
            },
          }}
        />
      </div>
    </aside>
  );
}
