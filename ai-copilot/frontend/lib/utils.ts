import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, isToday, isYesterday } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isToday(d)) return `Today at ${format(d, 'h:mm a')}`;
  if (isYesterday(d)) return `Yesterday at ${format(d, 'h:mm a')}`;
  return format(d, 'MMM d, yyyy h:mm a');
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

export function formatShortDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isToday(d)) return format(d, 'h:mm a');
  if (isYesterday(d)) return 'Yesterday';
  return format(d, 'MMM d');
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export const statusColors: Record<string, string> = {
  open: 'bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400',
  pending: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  resolved: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  closed: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  available: 'bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400',
  busy: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  offline: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  ready: 'bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400',
  processing: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  failed: 'bg-error-100 text-error-700 dark:bg-error-900/30 dark:text-error-400',
};

export const priorityColors: Record<string, string> = {
  low: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  medium: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  high: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  urgent: 'bg-error-100 text-error-700 dark:bg-error-900/30 dark:text-error-400',
};

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}
