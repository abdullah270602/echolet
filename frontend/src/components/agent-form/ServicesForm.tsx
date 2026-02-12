/**
 * Services Form - Manage services list
 */

import { Control, Controller, FieldErrors, useFieldArray } from 'react-hook-form';
import { Plus, Trash2 } from 'lucide-react';
import { Button, Input } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';

interface ServicesFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
}

export function ServicesForm({ control, errors }: ServicesFormProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'services',
  });

  const addService = () => {
    append({ name: '', price: '', duration_minutes: undefined });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-white/80">Services</h3>
          <p className="text-xs text-white/40 mt-1">
            Services your agent can discuss and book appointments for
          </p>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={addService}>
          <Plus className="w-4 h-4 mr-1" />
          Add Service
        </Button>
      </div>

      {fields.length === 0 ? (
        <div className="text-center py-8 border border-dashed border-white/20 rounded-lg">
          <p className="text-white/40 text-sm">No services added yet</p>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={addService}
            className="mt-2"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add your first service
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {fields.map((field, index) => (
            <div
              key={field.id}
              className="p-4 bg-white/5 rounded-lg border border-white/10 space-y-4"
            >
              <div className="flex items-start justify-between">
                <span className="text-sm font-medium text-white/60">
                  Service {index + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(index)}
                  className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Service Name */}
                <div className="space-y-1">
                  <label className="text-xs text-white/60">Name</label>
                  <Controller
                    name={`services.${index}.name`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        placeholder="e.g., Teeth Cleaning"
                        className={
                          errors.services?.[index]?.name ? 'border-red-400' : ''
                        }
                      />
                    )}
                  />
                </div>

                {/* Price */}
                <div className="space-y-1">
                  <label className="text-xs text-white/60">Price</label>
                  <Controller
                    name={`services.${index}.price`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        value={field.value || ''}
                        placeholder="e.g., $120"
                      />
                    )}
                  />
                </div>

                {/* Duration */}
                <div className="space-y-1">
                  <label className="text-xs text-white/60">Duration (min)</label>
                  <Controller
                    name={`services.${index}.duration_minutes`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        type="number"
                        value={field.value || ''}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value ? parseInt(e.target.value) : undefined
                          )
                        }
                        placeholder="e.g., 45"
                      />
                    )}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
