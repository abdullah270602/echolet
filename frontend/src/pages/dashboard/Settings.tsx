import { Cog, Clock } from 'lucide-react';

export function Settings() {
  return (
    <div className="max-w-4xl mx-auto flex items-center justify-center min-h-[calc(100vh-12rem)]">
      <div className="text-center border-2 border-ink bg-white p-8 sm:p-10 max-w-md w-full">
        <div className="w-16 h-16 mx-auto mb-6 bg-paper flex items-center justify-center border border-rule">
          <Cog className="w-8 h-8 text-accent" />
        </div>
        <h2 className="font-display text-2xl font-bold text-ink mb-2">Settings</h2>
        <p className="text-muted mb-6">
          Configure your account preferences, notifications, and integration settings.
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-paper border border-rule text-muted text-sm font-medium">
          <Clock className="w-4 h-4 text-accent" />
          Coming Soon
        </div>
      </div>
    </div>
  );
}
