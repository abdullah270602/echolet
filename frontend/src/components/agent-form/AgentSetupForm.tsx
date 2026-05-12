/**
 * Agent Setup Form - Identity and custom instructions
 */

import { Control, Controller, FieldErrors } from 'react-hook-form';
import { Input, Textarea } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';

interface AgentSetupFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
}

export function AgentSetupForm({ control, errors }: AgentSetupFormProps) {
  return (
    <div className="space-y-6">
      {/* Agent Name */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-ink">
          Agent Name <span className="text-red-700">*</span>
        </label>
        <Controller
          name="agent.name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              placeholder="e.g., Sarah"
              className={errors.agent?.name ? 'border-red-600' : ''}
            />
          )}
        />
        {errors.agent?.name && (
          <p className="text-sm text-red-700">{errors.agent.name.message}</p>
        )}
        <p className="text-xs text-muted">The name your agent will use to introduce itself</p>
      </div>

      {/* Business Name */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-ink">
          Business Name <span className="text-red-700">*</span>
        </label>
        <Controller
          name="agent.business_name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              placeholder="e.g., Echolet Dental Clinic"
              className={errors.agent?.business_name ? 'border-red-600' : ''}
            />
          )}
        />
        {errors.agent?.business_name && (
          <p className="text-sm text-red-700">{errors.agent.business_name.message}</p>
        )}
      </div>

      {/* Greeting Message */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-ink">
          Greeting Message <span className="text-red-700">*</span>
        </label>
        <Controller
          name="agent.greeting_message"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              placeholder="e.g., Hi! Thanks for calling Echolet Dental. How can I help you today?"
              rows={3}
              className={errors.agent?.greeting_message ? 'border-red-600' : ''}
            />
          )}
        />
        {errors.agent?.greeting_message && (
          <p className="text-sm text-red-700">{errors.agent.greeting_message.message}</p>
        )}
        <p className="text-xs text-muted">This is the first thing your agent will say</p>
      </div>

      {/* Custom Instructions */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-ink">
          Custom Instructions
        </label>
        <Controller
          name="custom_instructions"
          control={control}
          render={({ field }) => (
            <Textarea
              {...field}
              value={field.value || ''}
              placeholder="e.g., Always confirm appointment times before ending calls. Offer to take a message if the caller needs to speak with a specific person."
              rows={4}
            />
          )}
        />
        <p className="text-xs text-muted">Additional instructions for how your agent should behave</p>
      </div>
    </div>
  );
}
