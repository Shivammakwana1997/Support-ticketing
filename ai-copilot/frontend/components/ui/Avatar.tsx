import { cn, getInitials } from '@/lib/utils';

interface AvatarProps {
  name: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  status?: 'online' | 'offline' | 'busy';
  className?: string;
}

const sizeStyles = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-14 h-14 text-base',
};

const statusColors = {
  online: 'bg-accent-500',
  offline: 'bg-neutral-400',
  busy: 'bg-warning-500',
};

const statusSizes = {
  sm: 'w-2.5 h-2.5 border',
  md: 'w-3 h-3 border-2',
  lg: 'w-4 h-4 border-2',
};

export function Avatar({ name, src, size = 'md', status, className }: AvatarProps) {
  const initials = getInitials(name);

  return (
    <div className={cn('relative inline-flex shrink-0', className)}>
      {src ? (
        <img
          src={src}
          alt={name}
          className={cn(
            'rounded-full object-cover',
            sizeStyles[size]
          )}
        />
      ) : (
        <div
          className={cn(
            'rounded-full flex items-center justify-center font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
            sizeStyles[size]
          )}
        >
          {initials}
        </div>
      )}
      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 rounded-full border-white dark:border-neutral-800',
            statusColors[status],
            statusSizes[size]
          )}
        />
      )}
    </div>
  );
}
