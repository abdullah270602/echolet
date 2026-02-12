/**
 * Actions Form - STUB for future action triggers
 */

import { Zap, Calendar, Bell, Database } from 'lucide-react';
import { Button } from '../ui';

const AVAILABLE_ACTIONS = [
  {
    id: 'schedule_appointment',
    name: 'Schedule Appointment',
    description: 'Automatically book appointments based on caller requests',
    icon: Calendar,
    trigger: 'When caller requests an appointment',
    status: 'coming_soon',
  },
  {
    id: 'send_notification',
    name: 'Send Notification',
    description: 'Alert team members about urgent calls',
    icon: Bell,
    trigger: 'When call is marked as urgent',
    status: 'coming_soon',
  },
  {
    id: 'create_record',
    name: 'Create CRM Record',
    description: 'Automatically create customer records',
    icon: Database,
    trigger: 'When new caller is detected',
    status: 'coming_soon',
  },
];

export function ActionsForm() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-white/80">Actions & Triggers</h3>
          <p className="text-xs text-white/40 mt-1">
            Automate tasks based on call events
          </p>
        </div>
        <Button type="button" variant="ghost" size="sm" disabled>
          <Zap className="w-4 h-4 mr-1" />
          Add Action
        </Button>
      </div>

      <div className="space-y-4">
        {AVAILABLE_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <div
              key={action.id}
              className="p-4 bg-white/5 rounded-lg border border-white/10"
            >
              <div className="flex items-start gap-4">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Icon className="w-5 h-5 text-white/60" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-white/80">
                      {action.name}
                    </h4>
                    <span className="text-xs px-2 py-0.5 bg-yellow-400/20 text-yellow-400 rounded">
                      Coming Soon
                    </span>
                  </div>
                  <p className="text-xs text-white/40 mt-1">
                    {action.description}
                  </p>
                  <p className="text-xs text-white/30 mt-2">
                    <span className="text-white/50">Trigger:</span> {action.trigger}
                  </p>
                </div>
                <Button variant="ghost" size="sm" disabled>
                  Configure
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-4 bg-teal-400/10 border border-teal-400/20 rounded-lg">
        <p className="text-sm text-teal-400">
          Actions and triggers are coming soon! Define automated workflows that
          respond to call events in real-time.
        </p>
      </div>
    </div>
  );
}
