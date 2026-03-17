'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  Users, 
  Ticket, 
  MessageSquare, 
  BarChart3, 
  Settings,
  Headphones,
  Shield,
  Bot,
  Mail,
  Phone,
  TrendingUp,
  TrendingDown,
  ArrowUpRight
} from 'lucide-react';

const stats = [
  { label: 'Total Users', value: '2,456', change: '+12%', trend: 'up', icon: Users },
  { label: 'Active Tickets', value: '89', change: '-5%', trend: 'down', icon: Ticket },
  { label: 'Conversations', value: '5,678', change: '+23%', trend: 'up', icon: MessageSquare },
  { label: 'AI Resolution Rate', value: '78%', change: '+8%', trend: 'up', icon: Bot },
];

const agentStats = [
  { name: 'Sarah Johnson', conversations: 156, avgTime: '2.3m', satisfaction: 98, status: 'online' },
  { name: 'Mike Chen', conversations: 142, avgTime: '2.8m', satisfaction: 95, status: 'online' },
  { name: 'Emily Davis', conversations: 128, avgTime: '3.1m', satisfaction: 92, status: 'away' },
  { name: 'John Smith', conversations: 98, avgTime: '4.2m', satisfaction: 88, status: 'offline' },
];

const channels = [
  { name: 'Chat', icon: MessageSquare, count: 2340, percentage: 45 },
  { name: 'Email', icon: Mail, count: 1890, percentage: 36 },
  { name: 'WhatsApp', icon: Phone, count: 560, percentage: 11 },
  { name: 'Voice', icon: Phone, count: 340, percentage: 8 },
];

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Top Bar */}
      <header className="bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                  <Headphones className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-neutral-900 dark:text-white">SupportAI</span>
              </Link>
              <span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium rounded">Admin</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/admin/settings" className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
                <Settings className="w-5 h-5" />
              </Link>
              <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-medium">
                A
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">Admin Dashboard</h1>
          <p className="text-neutral-600 dark:text-neutral-400">Monitor your support operations</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <Icon className="w-8 h-8 text-primary-600" />
                  <span className={`flex items-center gap-1 text-sm font-medium ${
                    stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {stat.change}
                  </span>
                </div>
                <p className="text-3xl font-bold text-neutral-900 dark:text-white mb-1">{stat.value}</p>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">{stat.label}</p>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Agent Performance */}
          <div className="card">
            <div className="p-6 border-b border-neutral-200 dark:border-neutral-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Agent Performance</h2>
                <Link href="/admin/agents" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                  View all <ArrowUpRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
            <div className="divide-y divide-neutral-200 dark:divide-neutral-700">
              {agentStats.map((agent) => (
                <div key={agent.name} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center">
                      <span className="text-sm font-medium text-neutral-600 dark:text-neutral-300">
                        {agent.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-neutral-900 dark:text-white">{agent.name}</p>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">{agent.conversations} conv.</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <span className="text-neutral-500 dark:text-neutral-400">{agent.avgTime}</span>
                    <span className="text-green-600 font-medium">{agent.satisfaction}%</span>
                    <span className={`w-2 h-2 rounded-full ${
                      agent.status === 'online' ? 'bg-green-500' :
                      agent.status === 'away' ? 'bg-amber-500' : 'bg-neutral-400'
                    }`}></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Channels */}
          <div className="card">
            <div className="p-6 border-b border-neutral-200 dark:border-neutral-700">
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Channels</h2>
            </div>
            <div className="p-6 space-y-4">
              {channels.map((channel) => {
                const Icon = channel.icon;
                return (
                  <div key={channel.name}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon className="w-5 h-5 text-neutral-500" />
                        <span className="text-neutral-900 dark:text-white">{channel.name}</span>
                      </div>
                      <span className="text-neutral-600 dark:text-neutral-400">{channel.count}</span>
                    </div>
                    <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full gradient-primary rounded-full" 
                        style={{ width: `${channel.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link href="/admin/agents" className="card p-4 hover:shadow-lg transition-shadow">
            <Users className="w-8 h-8 text-primary-600 mb-3" />
            <p className="font-medium text-neutral-900 dark:text-white">Manage Agents</p>
          </Link>
          <Link href="/admin/tickets" className="card p-4 hover:shadow-lg transition-shadow">
            <Ticket className="w-8 h-8 text-amber-600 mb-3" />
            <p className="font-medium text-neutral-900 dark:text-white">All Tickets</p>
          </Link>
          <Link href="/admin/analytics" className="card p-4 hover:shadow-lg transition-shadow">
            <BarChart3 className="w-8 h-8 text-blue-600 mb-3" />
            <p className="font-medium text-neutral-900 dark:text-white">Analytics</p>
          </Link>
          <Link href="/admin/settings" className="card p-4 hover:shadow-lg transition-shadow">
            <Shield className="w-8 h-8 text-green-600 mb-3" />
            <p className="font-medium text-neutral-900 dark:text-white">Settings</p>
          </Link>
        </div>
      </div>
    </div>
  );
}