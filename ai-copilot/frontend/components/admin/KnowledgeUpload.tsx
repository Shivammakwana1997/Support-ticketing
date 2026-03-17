'use client';

import { useState, useRef, useCallback } from 'react';
import { Upload, Link, FileText, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { Document } from '@/types/knowledge';

interface KnowledgeUploadProps {
  documents?: Document[];
  onUpload?: (file: File) => Promise<void>;
  onIngestURL?: (url: string) => Promise<void>;
  onDelete?: (id: string) => void;
  isUploading?: boolean;
}

const statusVariant: Record<string, 'green' | 'yellow' | 'blue' | 'red' | 'gray'> = {
  ready: 'green',
  processing: 'blue',
  pending: 'yellow',
  failed: 'red',
};

const statusIcon: Record<string, React.ReactNode> = {
  ready: <CheckCircle2 className="w-4 h-4 text-accent-500" />,
  processing: <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />,
  pending: <Loader2 className="w-4 h-4 text-warning-500" />,
  failed: <AlertCircle className="w-4 h-4 text-error-500" />,
};

export function KnowledgeUpload({
  documents = [],
  onUpload,
  onIngestURL,
  onDelete,
  isUploading = false,
}: KnowledgeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && onUpload) {
        await onUpload(file);
      }
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && onUpload) {
        await onUpload(file);
      }
      if (e.target) e.target.value = '';
    },
    [onUpload]
  );

  const handleURLSubmit = async () => {
    if (urlInput.trim() && onIngestURL) {
      await onIngestURL(urlInput.trim());
      setUrlInput('');
    }
  };

  return (
    <div className="space-y-6">
      {/* File Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all',
          isDragging
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10'
            : 'border-neutral-300 dark:border-neutral-600 hover:border-primary-400 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.txt,.md,.docx,.csv,.json"
        />
        <Upload
          className={cn(
            'w-10 h-10 mx-auto mb-3',
            isDragging ? 'text-primary-500' : 'text-neutral-400'
          )}
        />
        <p className="text-sm font-medium text-neutral-900 dark:text-white mb-1">
          {isUploading ? 'Uploading...' : 'Drop files here or click to upload'}
        </p>
        <p className="text-xs text-neutral-500">
          PDF, TXT, Markdown, DOCX, CSV, JSON (max 50MB)
        </p>
      </div>

      {/* URL Input */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Input
            label="Ingest from URL"
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://example.com/docs/article"
          />
        </div>
        <Button
          onClick={handleURLSubmit}
          disabled={!urlInput.trim()}
          leftIcon={<Link className="w-4 h-4" />}
        >
          Ingest
        </Button>
      </div>

      {/* Document List */}
      {documents.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
            Documents ({documents.length})
          </h3>
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl"
              >
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-neutral-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                    {doc.title || doc.file_name || 'Untitled'}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant={statusVariant[doc.status] || 'gray'}>
                      {doc.status}
                    </Badge>
                    <span className="text-xs text-neutral-400">
                      {doc.chunk_count} chunks
                    </span>
                    <span className="text-xs text-neutral-400">
                      {formatRelativeTime(doc.created_at)}
                    </span>
                  </div>
                  {doc.error_message && (
                    <p className="text-xs text-error-500 mt-1">{doc.error_message}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {statusIcon[doc.status]}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(doc.id)}
                      className="p-1.5 rounded-lg text-neutral-400 hover:text-error-600 hover:bg-error-50 dark:hover:bg-error-900/20 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
