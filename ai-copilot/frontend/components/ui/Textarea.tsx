'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  showCount?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, showCount, maxLength, value, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');
    const charCount = typeof value === 'string' ? value.length : 0;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1.5"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          value={value}
          maxLength={maxLength}
          className={cn(
            'w-full px-3 py-2.5 rounded-lg border bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500 text-sm transition-colors duration-150 input-focus resize-y min-h-[80px]',
            error
              ? 'border-error-500 focus:ring-error-500/20 focus:border-error-500'
              : 'border-neutral-300 dark:border-neutral-600',
            className
          )}
          {...props}
        />
        <div className="flex justify-between mt-1.5">
          {error ? (
            <p className="text-xs text-error-600 dark:text-error-400">{error}</p>
          ) : (
            <span />
          )}
          {showCount && maxLength && (
            <p className="text-xs text-neutral-400">
              {charCount}/{maxLength}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
