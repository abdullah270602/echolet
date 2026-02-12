/**
 * Voice Form - Voice provider, voice selection, and speaking style
 */

import { Control, Controller, FieldErrors, useWatch } from 'react-hook-form';
import { Select } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';
import type { VoiceOption, SpeakingStyleOption } from '../../types/agent';

interface VoiceFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
  voices: VoiceOption[];
  speakingStyles: SpeakingStyleOption[];
}

const PROVIDER_OPTIONS = [
  { value: 'inworld', label: 'Inworld - High-quality, natural voices' },
  { value: 'deepgram', label: 'Deepgram - Fast, low-latency voices' },
];

const LANGUAGE_OPTIONS = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'es-ES', label: 'Spanish' },
  { value: 'fr-FR', label: 'French' },
  { value: 'de-DE', label: 'German' },
];

export function VoiceForm({ control, errors, voices, speakingStyles }: VoiceFormProps) {
  const selectedProvider = useWatch({ control, name: 'voice.provider' });

  // Filter voices by selected provider and map to select options
  const voiceOptions = voices
    .filter((v) => v.provider === selectedProvider)
    .map((v) => ({
      value: v.id,
      label: `${v.name} - ${v.gender}, ${v.description}`,
    }));

  // Map speaking styles to select options
  const styleOptions = speakingStyles.map((s) => ({
    value: s.id,
    label: `${s.name} - ${s.description}`,
  }));

  return (
    <div className="space-y-6">
      {/* Voice Provider */}
      <Controller
        name="voice.provider"
        control={control}
        render={({ field }) => (
          <Select
            label="Voice Provider"
            options={PROVIDER_OPTIONS}
            value={field.value}
            onChange={field.onChange}
            placeholder="Select a provider"
          />
        )}
      />

      {/* Voice Selection */}
      <Controller
        name="voice.voice_id"
        control={control}
        render={({ field }) => (
          <Select
            label="Voice"
            required
            options={voiceOptions}
            value={field.value}
            onChange={field.onChange}
            placeholder="Select a voice"
            error={errors.voice?.voice_id?.message}
          />
        )}
      />

      {/* Speaking Style */}
      <Controller
        name="voice.speaking_style"
        control={control}
        render={({ field }) => (
          <Select
            label="Speaking Style"
            options={styleOptions}
            value={field.value}
            onChange={field.onChange}
            placeholder="Select a style"
          />
        )}
      />
      <p className="text-xs text-white/40 -mt-4">How your agent should sound during calls</p>

      {/* Language */}
      <Controller
        name="voice.language"
        control={control}
        render={({ field }) => (
          <Select
            label="Language"
            options={LANGUAGE_OPTIONS}
            value={field.value}
            onChange={field.onChange}
            placeholder="Select language"
          />
        )}
      />
    </div>
  );
}
