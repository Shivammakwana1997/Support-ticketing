'use client';

import { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Star,
  Users,
  MessageSquare,
  Ticket,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { Tabs } from '@/components/ui/Tabs';
import { AnalyticsChart } from '@/components/admin/AnalyticsChart';
import { cn } from '@/lib/utils';

type TimeRange = '7d' | '30d' | '90d';

interface AnalyticsData {
  ticketsOverTime: { label: string; value: number }[];
  conversationsOverTime: { label: string; value: number }[];
  resolutionTime: { label: string; value: number }[];
  csatOverTime: { label: string; value: number }[];
  channelDistribution: { label: string; value: number }[];
  agentPerformance: {
    name: string;
    resolved: number;
    avgTime: string;
    csat: number;
  }[];
  summary: {
    totalTickets: number;
    ticketChange: number;
    totalConversations: number;
    convChange: number;
    avgResolutionTime: string;
    resTimeChange: number;
    avgCSAT: number;
    csatChange: number;
  };
}

const mockData: AnalyticsData = {
  ticketsOverTime: [
    { label: 'Week 1', value: 145 },
    { label: 'Week 2', value: 168 },
    { label: 'Week 3', value: 132 },
    { label: 'Week 4', value: 189 },
  ],
  conversationsOverTime: [
    { label: 'Week 1', value: 234 },
    { label: 'Week 2', value: 289 },
    { label: 'Week 3', value: 256 },
    { label: 'Week 4', value: 312 },
  ],
  resolutionTime: [
    { label: 'Mon', value: 4.2 },
    { label: 'Tue', value: 3.8 },
    { label: 'Wed', value: 5.1 },
    { label: 'Thu', value: 3.5 },
    { label: 'Fri', value: 4.0 },
    { label: 'Sat', value: 6.2 },
    { label: 'Sun', value: 5.8 },
  ],
  csatOverTime: [
    { label: 'Week 1', value: 4.3 },
    { label: 'Week 2', value: 4.5 },
    { label: 'Week 3', value: 4.4 },
    { label: 'Week 4', value: 4.7 },
  ],
  channelDistribution: [
    { label: 'Chat', value: 45 },
    { label: 'Email', value: 30 },
    { label: 'Slack', value: 15 },
    { label: 'API', value: 10 },
  ],
  agentPerformance: [
    { name: 'Sarah Chen', resolved: 45, avgTime: '3m 12s', csat: 4.8 },
    { name: 'Mike Johnson', resolved: 38, avgTime: '4m 05s', csat: 4.6 },
    { name: 'Emily Davis', resolved: 42, avgTime: '2m 45s', csat: 4.9 },
    { name: 'Alex Kim', resolved: 31, avgTime: '5m 30s', csat: 4.3 },
    { name: 'Jordan Lee', resolved: 36, avgTime: '3m 48s', csat: 4.5 },
  ],
  summary: {
    totalTickets: 634,
    ticketChange: 12,
    totalConversations: 1091,
    convChange: 8,
    avgResolutionTime: '4.1h',
    resTimeChange: -15,
    avgCSAT: 4.5,
    csatChange: 5,
  },
};

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    setTimeout(() => {
      setData(mockData);
      setIsLoading(false);
    }, 500);
  }, [timeRange]);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'tickets', label: 'Tickets' },
    { id: 'conversations', label: 'Conversations' },
    { id: 'agents', label: 'Agent Performance' },
  ];

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  const summaryCards = [
    {
      label: 'Total Tickets',
      value: data.summary.totalTickets,
      change: data.summary.ticketChange,
      icon: Ticket,
      color: 'text-primary-500',
      bgColor: 'bg-primary-50 dark:bg-primary-900/20',
    },
    {
      label: 'Total Conversations',
      value: data.summary.totalConversations,
      change: data.summary.convChange,
      icon: MessageSquare,
      color: 'text-accent-500',
      bgColor: 'bg-accent-50 dark:bg-accent-900/20',
    },
    {
      label: 'Avg Resolution Time',
      value: data.summary.avgResolutionTime,
      change: data.summary.resTimeChange,
      icon: Clock,
      color: 'text-warning-500',
      bgColor: 'bg-warning-50 dark:bg-warning-900/20',
    },
    {
      label: 'Avg CSAT',
      value: data.summary.avgCSAT,
      change: data.summary.csatChange,
      icon: Star,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            Analytics
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Insights and metrics across your support operations
          </p>
        </div>
        <div className="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1">
          {(['7d', '30d', '90d'] as TimeRange[]).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                timeRange === range
                  ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'
              )}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {summaryCards.map((stat) => {
          const Icon = stat.icon;
          const isPositive = stat.change > 0;
          const changeLabel = stat.label.includes('Resolution')
            ? !isPositive
            : isPositive;
          return (
            <Card key={stat.label}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider">
                      {stat.label}
                    </p>
                    <p className="text-2xl font-bold text-neutral-900 dark:text-white mt-1">
                      {typeof stat.value === 'number' && stat.value > 100
                        ? stat.value.toLocaleString()
                        : stat.value}
                    </p>
                    <div className="flex items-center gap-1 mt-1">
                      {changeLabel ? (
                        <ArrowUpRight className="w-3 h-3 text-accent-500" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3 text-error-500" />
                      )}
                      <span
                        className={cn(
                          'text-xs font-medium',
                          changeLabel ? 'text-accent-500' : 'text-error-500'
                        )}
                      >
                        {Math.abs(stat.change)}%
                      </span>
                      <span className="text-xs text-neutral-400">
                        vs prev period
                      </span>
                    </div>
                  </div>
                  <div
                    className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      stat.bgColor
                    )}
                  >
                    <Icon className={cn('w-5 h-5', stat.color)} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Tickets Over Time
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="bar"
                  data={data.ticketsOverTime}
                  dataKey="value"
                  xAxisKey="label"
                  height={280}
                  color="#3B82F6"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  CSAT Trend
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="line"
                  data={data.csatOverTime}
                  dataKey="value"
                  xAxisKey="label"
                  height={280}
                  color="#10B981"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Channel Distribution
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="pie"
                  data={data.channelDistribution}
                  dataKey="value"
                  xAxisKey="label"
                  height={280}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Resolution Time (hours)
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="line"
                  data={data.resolutionTime}
                  dataKey="value"
                  xAxisKey="label"
                  height={280}
                  color="#F59E0B"
                />
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'tickets' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Ticket Volume
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="bar"
                  data={data.ticketsOverTime}
                  dataKey="value"
                  xAxisKey="label"
                  height={350}
                  color="#3B82F6"
                />
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'conversations' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Conversation Volume
                </h2>
              </CardHeader>
              <CardContent>
                <AnalyticsChart
                  type="line"
                  data={data.conversationsOverTime}
                  dataKey="value"
                  xAxisKey="label"
                  height={350}
                  color="#10B981"
                />
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'agents' && (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                Agent Performance
              </h2>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-700">
                      <th className="text-left text-xs font-medium text-neutral-500 uppercase tracking-wider px-6 py-3">
                        Agent
                      </th>
                      <th className="text-left text-xs font-medium text-neutral-500 uppercase tracking-wider px-6 py-3">
                        Resolved
                      </th>
                      <th className="text-left text-xs font-medium text-neutral-500 uppercase tracking-wider px-6 py-3">
                        Avg Handle Time
                      </th>
                      <th className="text-left text-xs font-medium text-neutral-500 uppercase tracking-wider px-6 py-3">
                        CSAT
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                    {data.agentPerformance.map((agent) => (
                      <tr
                        key={agent.name}
                        className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-xs font-medium text-primary-600 dark:text-primary-400">
                              {agent.name
                                .split(' ')
                                .map((n) => n[0])
                                .join('')}
                            </div>
                            <span className="text-sm font-medium text-neutral-900 dark:text-white">
                              {agent.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-neutral-700 dark:text-neutral-300">
                          {agent.resolved}
                        </td>
                        <td className="px-6 py-4 text-sm text-neutral-700 dark:text-neutral-300">
                          {agent.avgTime}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-1">
                            <Star className="w-3.5 h-3.5 text-warning-500 fill-warning-500" />
                            <span className="text-sm font-medium text-neutral-900 dark:text-white">
                              {agent.csat}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
