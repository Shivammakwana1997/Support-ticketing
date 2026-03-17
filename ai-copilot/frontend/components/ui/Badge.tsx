import { cn } from '@/lib/utils';

type BadgeVariant = 'green' | 'red' | 'yellow' | 'blue' | 'gray' | 'purple';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  green: 'bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-400',
  red: 'bg-error-100 text-error-700 dark:bg-error-900/30 dark:text-error-400',
  yellow: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400',
  blue: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  gray: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
};

const dotColors: Record<BadgeVariant, string> = {
  green: 'bg-accent-500',
  red: 'bg-error-500',
  yellow: 'bg-warning-500',
  blue: 'bg-primary-500',
  gray: 'bg-neutral-400',
  purple: 'bg-purple-500',
};

export function Badge({ children, variant = 'gray', className, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} />}
      {children}
    </span>
  );
}
