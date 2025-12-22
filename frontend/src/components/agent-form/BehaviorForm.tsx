import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Briefcase, Smile, AlertCircle, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { Textarea, RadioTileGroup, Label } from '../ui';
import type { AgentFormData } from '../../schemas/agentSchema';

interface BehaviorFormProps {
  control: Control<AgentFormData>;
  errors: FieldErrors<AgentFormData>;
}

const TONE_OPTIONS = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Formal and business-like',
    icon: <Briefcase className="w-5 h-5" />,
  },
  {
    value: 'friendly',
    label: 'Friendly',
    description: 'Warm and approachable',
    icon: <Smile className="w-5 h-5" />,
  },
  {
    value: 'urgent',
    label: 'Urgent',
    description: 'Direct and action-oriented',
    icon: <AlertCircle className="w-5 h-5" />,
  },
];

export function BehaviorForm({ control, errors }: BehaviorFormProps) {
  const handleMagicEnhance = () => {
    toast('Magic Enhance coming soon!', {
      icon: '✨',
      duration: 2000,
    });
  };

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
            options={TONE_OPTIONS}
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
