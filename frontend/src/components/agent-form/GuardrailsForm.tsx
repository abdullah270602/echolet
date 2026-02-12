/**
 * Guardrails Form - Topic restrictions, compliance, and business hours
 */

import { useState } from 'react';
import { Control, Controller, FieldErrors, useFieldArray, useWatch } from 'react-hook-form';
import { Plus, X, Clock } from 'lucide-react';
import { Button, Input, Switch, Select } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';

interface GuardrailsFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
}

// DAYS_OF_WEEK will be used when schedule configuration is implemented
// const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const TIMEZONES = [
  { id: 'America/New_York', name: 'Eastern Time (ET)' },
  { id: 'America/Chicago', name: 'Central Time (CT)' },
  { id: 'America/Denver', name: 'Mountain Time (MT)' },
  { id: 'America/Los_Angeles', name: 'Pacific Time (PT)' },
  { id: 'UTC', name: 'UTC' },
];

export function GuardrailsForm({ control }: GuardrailsFormProps) {
  const [newAllowedTopic, setNewAllowedTopic] = useState('');
  const [newDisallowedTopic, setNewDisallowedTopic] = useState('');

  const { append: appendAllowed, remove: removeAllowed } = useFieldArray({
    control,
    name: 'guardrails.allowed_topics' as any,
  });

  const { append: appendDisallowed, remove: removeDisallowed } = useFieldArray({
    control,
    name: 'guardrails.disallowed_topics' as any,
  });

  // Schedule fields will be used when schedule configuration is implemented
  // const { fields: scheduleFields, update: updateSchedule } = useFieldArray({ control, name: 'guardrails.business_hours.schedule' as any });

  const businessHoursEnabled = useWatch({
    control,
    name: 'conversation.business_hours.enabled',
  });

  const allowedTopics = useWatch({ control, name: 'guardrails.allowed_topics' }) || [];
  const disallowedTopics = useWatch({ control, name: 'guardrails.disallowed_topics' }) || [];

  const addAllowedTopic = () => {
    const trimmed = newAllowedTopic.trim();
    if (trimmed && !allowedTopics.includes(trimmed)) {
      appendAllowed(trimmed as any);
      setNewAllowedTopic('');
    }
  };

  const addDisallowedTopic = () => {
    const trimmed = newDisallowedTopic.trim();
    if (trimmed && !disallowedTopics.includes(trimmed)) {
      appendDisallowed(trimmed as any);
      setNewDisallowedTopic('');
    }
  };

  return (
    <div className="space-y-8">
      {/* Topic Restrictions */}
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-medium text-white/80">Topic Guardrails</h3>
          <p className="text-xs text-white/40 mt-1">
            Control what topics your agent can and cannot discuss
          </p>
        </div>

        {/* Allowed Topics */}
        <div className="space-y-3">
          <label className="text-xs text-white/60">Allowed Topics (optional)</label>
          <div className="flex flex-wrap gap-2 min-h-[32px]">
            {allowedTopics.map((topic: string, index: number) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-3 py-1 bg-green-400/20 text-green-400 rounded-full text-sm"
              >
                {topic}
                <button type="button" onClick={() => removeAllowed(index)}>
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newAllowedTopic}
              onChange={(e) => setNewAllowedTopic(e.target.value)}
              placeholder="e.g., appointments, pricing"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addAllowedTopic();
                }
              }}
            />
            <Button type="button" variant="ghost" onClick={addAllowedTopic}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Disallowed Topics */}
        <div className="space-y-3">
          <label className="text-xs text-white/60">Disallowed Topics</label>
          <div className="flex flex-wrap gap-2 min-h-[32px]">
            {disallowedTopics.map((topic: string, index: number) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-3 py-1 bg-red-400/20 text-red-400 rounded-full text-sm"
              >
                {topic}
                <button type="button" onClick={() => removeDisallowed(index)}>
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newDisallowedTopic}
              onChange={(e) => setNewDisallowedTopic(e.target.value)}
              placeholder="e.g., medical advice, legal advice"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addDisallowedTopic();
                }
              }}
            />
            <Button type="button" variant="ghost" onClick={addDisallowedTopic}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-white/30">
            When asked about disallowed topics, your agent will try to redirect
            naturally, then politely decline if the caller persists.
          </p>
        </div>
      </div>

      {/* Compliance Settings */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-white/80">Compliance</h3>
          <p className="text-xs text-white/40 mt-1">
            Enable compliance modes for regulated industries
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div>
              <span className="text-sm text-white/80">HIPAA Mode</span>
              <p className="text-xs text-white/40">For healthcare providers</p>
            </div>
            <Controller
              name="guardrails.compliance.hipaa_mode"
              control={control}
              render={({ field }) => (
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>

          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div>
              <span className="text-sm text-white/80">GDPR Mode</span>
              <p className="text-xs text-white/40">For EU data protection</p>
            </div>
            <Controller
              name="guardrails.compliance.gdpr_mode"
              control={control}
              render={({ field }) => (
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>

          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div>
              <span className="text-sm text-white/80">Call Recording Disclaimer</span>
              <p className="text-xs text-white/40">Notify callers about recording</p>
            </div>
            <Controller
              name="guardrails.compliance.call_recording_disclaimer"
              control={control}
              render={({ field }) => (
                <Switch checked={field.value} onCheckedChange={field.onChange} />
              )}
            />
          </div>
        </div>
      </div>

      {/* Business Hours */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-white/80">Business Hours</h3>
            <p className="text-xs text-white/40 mt-1">
              Configure when your business is open
            </p>
          </div>
          <Controller
            name="conversation.business_hours.enabled"
            control={control}
            render={({ field }) => (
              <Switch checked={field.value} onCheckedChange={field.onChange} />
            )}
          />
        </div>

        {businessHoursEnabled && (
          <div className="space-y-4 p-4 bg-white/5 rounded-lg border border-white/10">
            {/* Timezone */}
            <Controller
              name="conversation.business_hours.timezone"
              control={control}
              render={({ field }) => (
                <Select
                  label="Timezone"
                  options={TIMEZONES.map((tz) => ({ value: tz.id, label: tz.name }))}
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Select timezone"
                />
              )}
            />

            {/* After Hours Behavior */}
            <Controller
              name="conversation.business_hours.after_hours_behavior"
              control={control}
              render={({ field }) => (
                <Select
                  label="After Hours Behavior"
                  options={[
                    { value: 'offer_callback', label: 'Offer to call back during business hours' },
                    { value: 'voicemail', label: 'Take a message' },
                  ]}
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Select behavior"
                />
              )}
            />

            <p className="text-xs text-white/30 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Schedule configuration coming soon
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
