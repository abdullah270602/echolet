/**
 * Integrations Form - STUB for future integrations
 */

import { Calendar, MessageSquare, Mail, ExternalLink } from 'lucide-react';
import { Button } from '../ui';

const AVAILABLE_INTEGRATIONS = [
  {
    id: 'google_calendar',
    name: 'Google Calendar',
    description: 'Schedule appointments directly to your calendar',
    icon: Calendar,
    status: 'coming_soon',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Send call notifications to your Slack workspace',
    icon: MessageSquare,
    status: 'coming_soon',
  },
  {
    id: 'email',
    name: 'Email',
    description: 'Send call summaries via email',
    icon: Mail,
    status: 'coming_soon',
  },
  {
    id: 'zendesk',
    name: 'Zendesk',
    description: 'Create support tickets from calls',
    icon: ExternalLink,
    status: 'coming_soon',
  },
];

export function IntegrationsForm() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-display text-base font-semibold text-ink">Integrations</h3>
        <p className="text-xs text-muted mt-1">
          Connect your agent to external services
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {AVAILABLE_INTEGRATIONS.map((integration) => {
          const Icon = integration.icon;
          return (
            <div
              key={integration.id}
              className="p-4 bg-paper/50 border border-rule flex items-start gap-4"
            >
              <div className="p-2 bg-white border border-rule">
                <Icon className="w-5 h-5 text-accent" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-ink">
                    {integration.name}
                  </h4>
                  <span className="text-xs px-2 py-0.5 bg-paper border border-rule text-muted font-medium">
                    Coming Soon
                  </span>
                </div>
                <p className="text-xs text-muted mt-1">
                  {integration.description}
                </p>
              </div>
              <Button variant="ghost" size="sm" disabled>
                Connect
              </Button>
            </div>
          );
        })}
      </div>

      <div className="p-4 bg-paper border border-rule">
        <p className="text-sm text-ink">
          Integrations are coming soon! We're working on connecting your agent to
          popular tools and services. Stay tuned for updates.
        </p>
      </div>
    </div>
  );
}
