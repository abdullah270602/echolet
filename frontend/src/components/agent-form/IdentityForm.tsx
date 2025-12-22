import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import { Input, Textarea, Select } from '../ui';
import { VoicePreviewButton } from './VoicePreviewButton';
import type { AgentFormData } from '../../schemas/agentSchema';
import type { VoiceOption } from '../../services/agentApi';

interface IdentityFormProps {
  control: Control<AgentFormData>;
  errors: FieldErrors<AgentFormData>;
  voices: VoiceOption[];
}

export function IdentityForm({ control, errors, voices }: IdentityFormProps) {
  // Map API voices to Select options format
  const voiceOptions = voices.map((v) => ({
    value: v.id,
    label: v.name,
  }));

  return (
    <div className="space-y-6">
      {/* Agent Name */}
      <Controller
        name="name"
        control={control}
        render={({ field }) => (
          <Input
            {...field}
            label="Agent Name"
            placeholder="e.g., Primary Receptionist"
            hint="A friendly name to identify this agent"
            error={errors.name?.message}
          />
        )}
      />

      {/* Business Name */}
      <Controller
        name="businessName"
        control={control}
        render={({ field }) => (
          <Input
            {...field}
            label="Business Name"
            required
            placeholder="e.g., Acme Corporation"
            hint="The name of your business or organization"
            error={errors.businessName?.message}
          />
        )}
      />

      {/* Greeting Message */}
      <Controller
        name="greetingMessage"
        control={control}
        render={({ field }) => (
          <Textarea
            {...field}
            label="Greeting Message"
            placeholder="Hello! Thank you for calling Acme Corporation. How can I assist you today?"
            hint="The first thing the agent will say when answering a call"
            minHeight={80}
            error={errors.greetingMessage?.message}
          />
        )}
      />

      {/* Voice Selection */}
      <Controller
        name="voiceId"
        control={control}
        render={({ field }) => (
          <div className="space-y-1">
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <Select
                  label="Voice"
                  options={voiceOptions}
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Select a voice"
                  error={errors.voiceId?.message}
                />
              </div>
              <VoicePreviewButton voiceId={field.value} />
            </div>
            <p className="text-xs text-white/40">
              Choose the voice your agent will use when speaking
            </p>
          </div>
        )}
      />
    </div>
  );
}
