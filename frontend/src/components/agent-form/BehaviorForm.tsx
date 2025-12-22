import { useMemo } from 'react';
import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Briefcase, Smile, AlertCircle, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { Textarea, RadioTileGroup, Label } from '../ui';
import type { AgentFormData } from '../../schemas/agentSchema';
import type { ToneOption } from '../../services/agentApi';

interface BehaviorFormProps {
  control: Control<AgentFormData>;
  errors: FieldErrors<AgentFormData>;
  tones: ToneOption[];
}

// Map tone IDs to icons
const TONE_ICONS: Record<string, React.ReactNode> = {
  professional: <Briefcase className="w-5 h-5" />,
  friendly: <Smile className="w-5 h-5" />,
  urgent: <AlertCircle className="w-5 h-5" />,
};

export function BehaviorForm({ control, errors, tones }: BehaviorFormProps) {
  const handleMagicEnhance = () => {
    toast('Magic Enhance coming soon!', {
      icon: '✨',
      duration: 2000,
    });
  };

  // Map API tones to RadioTileGroup options format
  const toneOptions = useMemo(() =>
    tones.map((t) => ({
      value: t.id,
      label: t.name,
      description: t.description,
      icon: TONE_ICONS[t.id] || <Briefcase className="w-5 h-5" />,
    })),
    [tones]
  );

  return (
    <div className="space-y-6">
      {/* Tone Selection */}
      <Controller
        name="tone"
        control={control}
        render={({ field }) => (
          <RadioTileGroup
            name="tone"
            label="Conversation Tone"
            options={toneOptions}
            value={field.value}
            onChange={field.onChange}
            error={errors.tone?.message}
          />
        )}
      />

      {/* Custom Instructions */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <Label>Custom Instructions</Label>
          <motion.button
            type="button"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleMagicEnhance}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
              bg-purple-500/10 border border-purple-500/20 text-purple-400
              hover:bg-purple-500/20 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Magic Enhance
          </motion.button>
        </div>

        <Controller
          name="customInstructions"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              placeholder={`Add specific instructions for how the agent should behave...

Examples:
• Always confirm the caller's name before proceeding
• Offer to schedule a callback if wait time exceeds 5 minutes
• Never discuss pricing without manager approval
• Use the caller's name at least twice during the conversation`}
              minHeight={200}
              error={errors.customInstructions?.message}
            />
          )}
        />

        <p className="text-xs text-white/40">
          Provide detailed instructions to customize your agent's behavior
        </p>
      </div>
    </div>
  );
}
