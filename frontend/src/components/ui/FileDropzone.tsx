import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, X } from 'lucide-react';
import { Label } from './Label';

interface FileDropzoneProps {
  accept?: string[];
  onFilesChange: (files: File[]) => void;
  files: File[];
  maxFiles?: number;
  maxSize?: number; // in bytes
  label?: string;
  hint?: string;
  error?: string;
  className?: string;
}

export function FileDropzone({
  accept = ['.pdf', '.txt'],
  onFilesChange,
  files,
  maxFiles = 5,
  maxSize = 5 * 1024 * 1024, // 5MB default
  label,
  hint,
  error,
  className = '',
}: FileDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragActive(true);
    }
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const validateFile = (file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!accept.includes(extension)) {
      return `File type ${extension} is not supported`;
    }
    if (file.size > maxSize) {
      return `File size exceeds ${formatFileSize(maxSize)}`;
    }
    return null;
  };

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;

      const validFiles: File[] = [];
      const remainingSlots = maxFiles - files.length;

      for (let i = 0; i < Math.min(newFiles.length, remainingSlots); i++) {
        const file = newFiles[i];
        const error = validateFile(file);
        if (!error) {
          validFiles.push(file);
        }
      }

      if (validFiles.length > 0) {
        onFilesChange([...files, ...validFiles]);
      }
    },
    [files, maxFiles, onFilesChange, accept, maxSize]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    e.target.value = ''; // Reset input
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const canAddMore = files.length < maxFiles;

  return (
    <div className={className}>
      {label && <Label className="mb-3">{label}</Label>}

      {/* Dropzone */}
      {canAddMore && (
        <div
          onDragEnter={handleDragIn}
          onDragLeave={handleDragOut}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-xl p-8
            transition-all duration-200 cursor-pointer
            ${isDragActive
              ? 'border-teal-500 bg-teal-500/5'
              : 'border-white/20 hover:border-white/30 hover:bg-white/5'
            }
            ${error ? 'border-red-500/50' : ''}
          `}
        >
          <input
            type="file"
            accept={accept.join(',')}
            onChange={handleInputChange}
            multiple={maxFiles > 1}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <div className="flex flex-col items-center text-center">
            <motion.div
              animate={isDragActive ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
              className={`
                w-12 h-12 rounded-xl flex items-center justify-center mb-3
                ${isDragActive ? 'bg-teal-500/20' : 'bg-white/10'}
              `}
            >
              <Upload
                className={`w-6 h-6 ${isDragActive ? 'text-teal-400' : 'text-white/50'}`}
              />
            </motion.div>

            <p className="text-sm text-white/70 mb-1">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-xs text-white/40">
              or click to browse ({accept.join(', ')})
            </p>
          </div>
        </div>
      )}

      {hint && !error && (
        <p className="text-xs text-white/40 mt-2">{hint}</p>
      )}

      {error && (
        <p className="text-xs text-red-400 mt-2">{error}</p>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, index) => (
            <motion.div
              key={`${file.name}-${index}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10"
            >
              <div className="w-8 h-8 rounded-lg bg-teal-500/20 flex items-center justify-center">
                <FileText className="w-4 h-4 text-teal-400" />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{file.name}</p>
                <p className="text-xs text-white/40">{formatFileSize(file.size)}</p>
              </div>

              <button
                type="button"
                onClick={() => removeFile(index)}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4 text-white/50 hover:text-white" />
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {/* File count indicator */}
      {files.length > 0 && (
        <p className="text-xs text-white/40 mt-2">
          {files.length} of {maxFiles} files uploaded
        </p>
      )}
    </div>
  );
}
