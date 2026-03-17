'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, 
  Ticket, 
  Users, 
  BarChart3, 
  Settings,
  Headphones,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  LogOut,
  Loader2
} from 'lucide-react';
import { createClient } from '@/lib/supabase';
import { useAuth } from '@/hooks/useAuth';

interface DashboardStats {
  totalConversations: number;
  openTickets: number;
  activeUsers: number;
  avgResponseTime: string;
}

interface RecentConversation {
  id: string;
  customer: string;
  subject: string;
  status: 'open' | 'resolved' | 'pending';
  time: string;
}

const quickActions = [
  { label: 'Start New Chat', icon: MessageSquare, href: '/user/chat', color: 'bg-primary-600' },
  { label: 'Create Ticket', icon: Ticket, href: '/user/tickets/new', color: 'bg-amber-600' },
  { label: 'View Analytics', icon: BarChart3, href: '/user/analytics', color: 'bg-blue-600' },
  { label: 'Settings', icon: Settings, href: '/user/settings', color: 'bg-neutral-600' },
];

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalConversations: 0,
    openTickets: 0,
    activeUsers: 0,
    avgResponseTime: '0m',
  });
  const [recentConversations, setRecentConversations] = useState<RecentConversation[]>([]);
  const [loading, setLoading] = useState(true);
  
  const { user, logout } = useAuth();
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch conversations count
        const { count: conversationsCount } = await supabase
          .from('conversations')
          .select('*', { count: 'exact', head: true });
        
        // Fetch open tickets count
        const { count: ticketsCount } = await supabase
          .from('tickets')
          .select('*', { count: 'exact', head: true })
          .eq('status', 'open');

        // Fetch active customers (users who had activity in last 24h)
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const { count: activeUsersCount } = await supabase
          .from('customers')
          .select('*', { count: 'exact', head: true })
          .gte('last_seen_at', yesterday.toISOString());

        // Fetch recent conversations
        const { data: conversationsData } = await supabase
          .from('conversations')
          .select('*, customer:customers(name)')
          .order('created_at', { ascending: false })
          .limit(5);

        if (conversationsData) {
          setRecentConversations(conversationsData.map((conv: any) => ({
            id: conv.id,
            customer: conv.customer?.name || 'Unknown',
            subject: conv.subject || 'No subject',
            status: conv.status || 'pending',
            time: getRelativeTime(conv.created_at),
          })));
        }

        setStats({
          totalConversations: conversationsCount || 0,
          openTickets: ticketsCount || 0,
          activeUsers: activeUsersCount || 0,
          avgResponseTime: '2.3m', // Default, could be calculated from actual data
        });
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        // Set default values on error
        setRecentConversations([
          { id: '1', customer: 'Demo User', subject: 'Welcome to SupportAI', status: 'open', time: 'Just now' },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [supabase]);

  const handleLogout = async () => {
    await logout();
    router.push('/auth/login');
  };

  const getRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const getUserInitials = (name: string): string => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const statsData = [
    { label: 'Total Conversations', value: stats.totalConversations.toLocaleString(), icon: MessageSquare, color: 'text-primary-600' },
    { label: 'Open Tickets', value: stats.openTickets.toString(), icon: Ticket, color: 'text-amber-600' },
    { label: 'Active Users', value: stats.activeUsers.toLocaleString(), icon: Users, color: 'text-green-600' },
    { label: 'Avg Response Time', value: stats.avgResponseTime, icon: Clock, color: 'text-blue-600' },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} fixed left-0 top-0 h-screen bg-white dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700 transition-all duration-300 z-40`}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-200 dark:border-neutral-700">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Headphones className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && <span className="font-bold text-neutral-900 dark:text-white">SupportAI</span>}
          </Link>
        </div>
        
        <nav className="p-4 space-y-2">
          <Link href="/user/dashboard" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
            <BarChart3 className="w-5 h-5" />
            {sidebarOpen && <span>Dashboard</span>}
          </Link>
          <Link href="/user/conversations" className="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700">
            <MessageSquare className="w-5 h-5" />
            {sidebarOpen && <span>Conversations</span>}
          </Link>
          <Link href="/user/tickets" className="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700">
            <Ticket className="w-5 h-5" />
            {sidebarOpen && <span>Tickets</span>}
          </Link>
          <Link href="/user/customers" className="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700">
            <Users className="w-5 h-5" />
            {sidebarOpen && <span>Customers</span>}
          </Link>
          <Link href="/user/analytics" className="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700">
            <BarChart3 className="w-5 h-5" />
            {sidebarOpen && <span>Analytics</span>}
          </Link>
          <Link href="/user/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-700">
            <Settings className="w-5 h-5" />
            {sidebarOpen && <span>Settings</span>}
          </Link>
        </nav>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-20'} transition-all duration-300`}>
        {/* Header */}
        <header className="h-16 bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between px-6">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center gap-4">
            <Link href="/user/chat" className="btn-primary">
              New Conversation
            </Link>
            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-medium">
              JD
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="p-6">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white mb-6">Dashboard</h1>
          
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statsData.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Icon className={`w-8 h-8 ${stat.color}`} />
                    <span className="text-3xl font-bold text-neutral-900 dark:text-white">{stat.value}</span>
                  </div>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">{stat.label}</p>
                </div>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link key={action.label} href={action.href} className="card p-4 hover:shadow-lg transition-shadow">
                  <div className={`w-10 h-10 rounded-lg ${action.color} flex items-center justify-center mb-3`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">{action.label}</p>
                </Link>
              );
            })}
          </div>

          {/* Recent Conversations */}
          <div className="card">
            <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Recent Conversations</h2>
              <Link href="/user/conversations" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                View all <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="divide-y divide-neutral-200 dark:divide-neutral-700">
              {recentConversations.map((conv) => (
                <div key={conv.id} className="p-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-neutral-700/50">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center">
                      <span className="text-sm font-medium text-neutral-600 dark:text-neutral-300">
                        {conv.customer.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-neutral-900 dark:text-white">{conv.customer}</p>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">{conv.subject}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      conv.status === 'open' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      conv.status === 'resolved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    }`}>
                      {conv.status === 'open' && <AlertCircle className="w-3 h-3" />}
                      {conv.status === 'resolved' && <CheckCircle2 className="w-3 h-3" />}
                      {conv.status}
                    </span>
                    <span className="text-sm text-neutral-500 dark:text-neutral-400">{conv.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}