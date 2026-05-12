/**
 * Knowledge Base Form - Manage text and URL knowledge sources
 */

import { Control, Controller, FieldErrors, useFieldArray } from 'react-hook-form';
import { Trash2, FileText, Globe } from 'lucide-react';
import { Button, Input, Textarea } from '../ui';
import type { AgentConfigFormData } from '../../schemas/agentSchema';

interface KnowledgeBaseFormProps {
  control: Control<AgentConfigFormData>;
  errors: FieldErrors<AgentConfigFormData>;
}

export function KnowledgeBaseForm({ control }: KnowledgeBaseFormProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'knowledge_base.sources',
  });

  const addTextSource = () => {
    append({ type: 'text', name: '', content: '' });
  };

  const addWebsiteSource = () => {
    append({ type: 'website', name: '', url: '' });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-display text-base font-semibold text-ink">Knowledge Sources</h3>
          <p className="text-xs text-muted mt-1">
            Information your agent can reference during calls
          </p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={addTextSource}>
            <FileText className="w-4 h-4 mr-1" />
            Add Text
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={addWebsiteSource}>
            <Globe className="w-4 h-4 mr-1" />
            Add URL
          </Button>
        </div>
      </div>

      {fields.length === 0 ? (
        <div className="text-center py-8 border border-dashed border-rule bg-paper/40">
          <p className="text-muted text-sm">No knowledge sources added yet</p>
          <div className="flex justify-center gap-2 mt-2">
            <Button type="button" variant="ghost" size="sm" onClick={addTextSource}>
              <FileText className="w-4 h-4 mr-1" />
              Add Text
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={addWebsiteSource}>
              <Globe className="w-4 h-4 mr-1" />
              Add URL
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {fields.map((field, index) => (
            <div
              key={field.id}
              className="p-4 bg-paper/50 border border-rule space-y-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {field.type === 'text' ? (
                    <FileText className="w-4 h-4 text-accent" />
                  ) : (
                    <Globe className="w-4 h-4 text-accent" />
                  )}
                  <span className="text-sm font-semibold text-ink">
                    {field.type === 'text' ? 'Text Source' : 'Website Reference'}
                  </span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => remove(index)}
                  className="text-red-700 hover:text-red-800 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              {/* Source Name */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted">Name</label>
                <Controller
                  name={`knowledge_base.sources.${index}.name`}
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      placeholder="e.g., Refund Policy"
                    />
                  )}
                />
              </div>

              {/* Content or URL based on type */}
              {field.type === 'text' ? (
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted">Content</label>
                  <Controller
                    name={`knowledge_base.sources.${index}.content`}
                    control={control}
                    render={({ field }) => (
                      <Textarea
                        {...field}
                        value={field.value || ''}
                        placeholder="Enter the knowledge text..."
                        rows={4}
                      />
                    )}
                  />
                </div>
              ) : (
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted">URL</label>
                  <Controller
                    name={`knowledge_base.sources.${index}.url`}
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        value={field.value || ''}
                        type="url"
                        placeholder="https://example.com/info"
                      />
                    )}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
