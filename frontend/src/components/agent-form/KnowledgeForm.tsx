import { Controller, type Control, type FieldErrors } from 'react-hook-form';
import { Tabs, TabsList, TabsTrigger, TabsContent, FileDropzone, Textarea, ProgressBar } from '../ui';
import type { AgentFormData } from '../../schemas/agentSchema';

interface KnowledgeFormProps {
  control: Control<AgentFormData>;
  errors: FieldErrors<AgentFormData>;
  files: File[];
  onFilesChange: (files: File[]) => void;
  tokenCount: number;
  tokenLimit: number;
}

export function KnowledgeForm({
  control,
  errors,
  files,
  onFilesChange,
  tokenCount,
  tokenLimit,
}: KnowledgeFormProps) {
  const formatTokens = (value: number, max: number) => {
    return `${value.toLocaleString()} / ${max.toLocaleString()} tokens`;
  };

  return (
    <div className="space-y-6">
      {/* Knowledge Source Tabs */}
      <Tabs defaultValue="upload">
        <TabsList className="mb-4">
          <TabsTrigger value="upload">Upload Files</TabsTrigger>
          <TabsTrigger value="text">Paste Text</TabsTrigger>
        </TabsList>

        <TabsContent value="upload">
          <FileDropzone
            files={files}
            onFilesChange={onFilesChange}
            accept={['.pdf', '.txt']}
            maxFiles={5}
            maxSize={5 * 1024 * 1024}
            hint="Upload PDF or TXT files containing FAQs, product info, or other knowledge"
          />
        </TabsContent>

        <TabsContent value="text">
          <Controller
            name="knowledgeText"
            control={control}
            render={({ field }) => (
              <Textarea
                {...field}
                placeholder={`Paste your FAQs, product information, or other knowledge here...

Example:
Q: What are your business hours?
A: We are open Monday through Friday, 9 AM to 5 PM EST.

Q: How do I reset my password?
A: Click the "Forgot Password" link on the login page and follow the instructions sent to your email.

Q: What is your return policy?
A: We offer a 30-day money-back guarantee on all products.`}
                minHeight={250}
                error={errors.knowledgeText?.message}
              />
            )}
          />
        </TabsContent>
      </Tabs>

      {/* Token Usage */}
      <div className="pt-4 border-t border-white/10">
        <ProgressBar
          value={tokenCount}
          max={tokenLimit}
          label="Context Usage"
          formatValue={formatTokens}
        />
        <p className="text-xs text-white/40 mt-2">
          The knowledge you provide counts towards your context limit.
          More context allows for better, more informed responses.
        </p>
      </div>
    </div>
  );
}
