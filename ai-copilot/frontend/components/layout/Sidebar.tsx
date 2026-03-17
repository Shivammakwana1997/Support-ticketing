'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Avatar } from '@/components/ui/Avatar';
import {
  Headphones,
  MessageSquare,
  Ticket,
  HelpCircle,
  History,
  LayoutDashboard,
  MessagesSquare,
  BookOpen,
  Users,
  Brain,
  Key,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import type { UserRole } from '@/types/user';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const userNavItems: NavItem[] = [
  { label: 'Chat', href: '/chat', icon: <MessageSquare className="w-5 h-5" /> },
  { label: 'Tickets', href: '/tickets', icon: <Ticket className="w-5 h-5" /> },
  { label: 'Help Center', href: '/help', icon: <HelpCircle className="w-5 h-5" /> },
  { label: 'History', href: '/history', icon: <History className="w-5 h-5" /> },
];

const agentNavItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'Conversations', href: '/conversations', icon: <MessagesSquare className="w-5 h-5" /> },
  { label: 'Tickets', href: '/tickets', icon: <Ticket className="w-5 h-5" /> },
];

const adminNavItems: NavItem[] = [
  { label: 'Dashboard', href: '/admin', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'Knowledge Base', href: '/admin/knowledge', icon: <BookOpen className="w-5 h-5" /> },
  { label: 'Agents', href: '/admin/agents', icon: <Users className="w-5 h-5" /> },
  { label: 'AI Config', href: '/admin/ai-config', icon: <Brain className="w-5 h-5" /> },
  { label: 'API Keys', href: '/admin/api-keys', icon: <Key className="w-5 h-5" /> },
  { label: 'Analytics', href: '/admin/analytics', icon: <BarChart3 className="w-5 h-5" /> },
  { label: 'Settings', href: '/admin/settings', icon: <Settings className="w-5 h-5" /> },
];

interface SidebarProps {
  role?: UserRole;
  userName?: string;
  userEmail?: string;
  onLogout?: () => void;
}

export function Sidebar({ role = 'viewer', userName = 'User', userEmail = '', onLogout }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const navItems =
    role === 'admin' ? adminNavItems : role === 'agent' ? agentNavItems : userNavItems;

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-800 flex flex-col transition-all duration-300 z-40',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-16 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
          <Headphones className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <span className="text-lg font-bold text-neutral-900 dark:text-white truncate">
            SupportAI
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 scrollbar-thin">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-neutral-200'
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <span className="shrink-0">{item.icon}</span>
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-neutral-200 dark:border-neutral-800 p-3 shrink-0">
        <div className="flex items-center gap-3">
          <Avatar name={userName} size="sm" status="online" />
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                {userName}
              </p>
              <p className="text-xs text-neutral-500 truncate">{userEmail}</p>
            </div>
          )}
          {!collapsed && onLogout && (
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-error-600 hover:bg-error-50 dark:hover:bg-error-900/20 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 flex items-center justify-center text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 shadow-sm transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-3.5 h-3.5" />
        ) : (
          <ChevronLeft className="w-3.5 h-3.5" />
        )}
      </button>
    </aside>
  );
}
