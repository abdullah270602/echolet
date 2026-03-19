/**
 * Ticket Output Form - Configure which fields to extract from calls
 */

import { useState } from 'react';
import { Control, Controller, FieldErrors, useController, useFieldArray, useWatch } from 'react-hook-form';
import { Plus, X } from 'lucide-react';
import { Button, Input, Switch } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';
import type { TicketField } from '../../types/agent';

interface TicketOutputFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
  defaultFields: TicketField[];
  suggestedTags: string[];
}

export function TicketOutputForm({
  control,
  defaultFields,
  suggestedTags,
}: TicketOutputFormProps) {
  const [newTag, setNewTag] = useState('');

  const { fields: ticketFields, replace } = useFieldArray({
    control,
    name: 'output.ticket_fields',
  });

  const { field: tagsField } = useController({ control, name: 'output.custom_tags' });
  const appendTag = (v: string) => tagsField.onChange([...(tagsField.value ?? []), v]);
  const removeTag = (i: number) =>
    tagsField.onChange((tagsField.value ?? []).filter((_, idx) => idx !== i));

  const currentTags = useWatch({ control, name: 'output.custom_tags' }) || [];

  // Initialize ticket fields from defaults if empty
  if (ticketFields.length === 0 && defaultFields.length > 0) {
    replace(defaultFields);
  }

  const addTag = () => {
    const trimmed = newTag.trim().toLowerCase().replace(/\s+/g, '_');
    if (trimmed && !currentTags.includes(trimmed)) {
      appendTag(trimmed);
      setNewTag('');
    }
  };

  const handleSuggestedTag = (tag: string) => {
    if (!currentTags.includes(tag)) {
      appendTag(tag);
    }
  };

  return (
    <div className="space-y-8">
      {/* Ticket Fields Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-white/80">Output Fields</h3>
          <p className="text-xs text-white/40 mt-1">
            Choose which information to extract from calls
          </p>
        </div>

        <div className="space-y-2">
          {ticketFields.map((field, index) => (
            <div
              key={field.id}
              className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"
            >
              <div className="flex items-center gap-3">
                <Controller
                  name={`output.ticket_fields.${index}.enabled`}
                  control={control}
                  render={({ field: switchField }) => (
                    <Switch
                      checked={switchField.value}
                      onCheckedChange={switchField.onChange}
                      disabled={field.required}
                    />
                  )}
                />
                <div>
                  <span className="text-sm text-white/80">{field.label}</span>
                  {field.required && (
                    <span className="ml-2 text-xs text-white/40">(Required)</span>
                  )}
                </div>
              </div>
              <span className="text-xs text-white/30 capitalize">{field.type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Tags Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-white/80">Custom Tags</h3>
          <p className="text-xs text-white/40 mt-1">
            Tags for categorizing and filtering calls
          </p>
        </div>

        {/* Current Tags */}
        <div className="flex flex-wrap gap-2">
          {currentTags.map((tag: string, index: number) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-teal-400/20 text-teal-400 rounded-full text-sm"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(index)}
                className="hover:text-teal-200"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>

        {/* Add New Tag */}
        <div className="flex gap-2">
          <Input
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            placeholder="Enter a custom tag"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addTag();
              }
            }}
          />
          <Button type="button" variant="ghost" onClick={addTag}>
            <Plus className="w-4 h-4" />
          </Button>
        </div>

        {/* Suggested Tags */}
        <div>
          <p className="text-xs text-white/40 mb-2">Suggested tags:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedTags
              .filter((tag) => !currentTags.includes(tag))
              .map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleSuggestedTag(tag)}
                  className="px-3 py-1 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 rounded-full text-xs transition-colors"
                >
                  + {tag}
                </button>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
