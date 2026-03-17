'use client';

import Link from 'next/link';
import {
  MessageSquare,
  Shield,
  Zap,
  BarChart3,
  Bot,
  Headphones,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';

const features = [
  {
    icon: Bot,
    title: 'AI-Powered Responses',
    description: 'Intelligent chatbot resolves common issues instantly using your knowledge base.',
  },
  {
    icon: Zap,
    title: 'Smart Routing',
    description: 'Automatically route tickets to the right agent based on skills and availability.',
  },
  {
    icon: Headphones,
    title: 'Omnichannel Support',
    description: 'Chat, email, WhatsApp, SMS, Slack, and Teams — all in one place.',
  },
  {
    icon: Shield,
    title: 'Agent Copilot',
    description: 'AI assists agents with suggested replies, KB retrieval, and ticket summaries.',
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Track CSAT, resolution times, agent performance, and AI effectiveness.',
  },
  {
    icon: MessageSquare,
    title: 'Knowledge Base RAG',
    description: 'Upload documents and let AI retrieve relevant answers for every query.',
  },
];

const stats = [
  { value: '70%', label: 'Faster Resolution' },
  { value: '24/7', label: 'AI Availability' },
  { value: '95%', label: 'Customer Satisfaction' },
  { value: '50%', label: 'Cost Reduction' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-neutral-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-neutral-200/50 dark:border-neutral-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                <Headphones className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-neutral-900 dark:text-white">
                SupportAI
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-50/50 to-transparent dark:from-primary-950/20 dark:to-transparent" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary-400/10 dark:bg-primary-500/5 rounded-full blur-3xl" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium mb-8">
            <Zap className="w-4 h-4" />
            Powered by Advanced AI
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-neutral-900 dark:text-white tracking-tight mb-6">
            AI Customer Support
            <br />
            <span className="text-gradient">Copilot</span>
          </h1>
          <p className="text-xl text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Resolve customer issues faster with intelligent AI that works alongside your team.
            Smart routing, instant answers, and real-time analytics — all in one platform.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-white gradient-primary hover:opacity-90 rounded-xl shadow-lg shadow-primary-500/25 transition-all hover:shadow-xl hover:shadow-primary-500/30"
            >
              <MessageSquare className="w-5 h-5" />
              Start Chat
            </Link>
            <Link
              href="/admin"
              className="inline-flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-neutral-700 dark:text-neutral-300 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 rounded-xl border border-neutral-200 dark:border-neutral-700 shadow-sm transition-all"
            >
              Admin Dashboard
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 border-y border-neutral-200/50 dark:border-neutral-800/50 bg-white/50 dark:bg-neutral-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold text-primary-600 dark:text-primary-400">
                  {stat.value}
                </div>
                <div className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-neutral-900 dark:text-white mb-4">
              Everything you need for world-class support
            </h2>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
              From AI-powered chat to analytics, get a complete customer support solution.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="group p-6 rounded-2xl bg-white dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700/50 card-hover"
                >
                  <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4 group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
                    <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative rounded-3xl gradient-hero p-12 text-center overflow-hidden">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjA1Ij48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnYtMmgtNHYyaC0ydjRoLTJ2MmgydjRoMnYyaDR2LTJoMnYtNGgydi0yem0wLTMwaDJ2LTRoLTJ6TTI0IDRoMnYtNGgtMnpNMTIgNGgydi00aC0yek0wIDRoMnYtNEgweiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
            <div className="relative">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Ready to transform your support?
              </h2>
              <p className="text-lg text-primary-100 mb-8 max-w-xl mx-auto">
                Join teams delivering faster, smarter customer support with AI.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-primary-600 bg-white hover:bg-primary-50 rounded-xl transition-colors"
                >
                  Get Started Free
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </div>
              <div className="flex items-center justify-center gap-6 mt-8 text-sm text-primary-200">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Free trial
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> No credit card
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Setup in minutes
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-neutral-200 dark:border-neutral-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-neutral-500">
          &copy; {new Date().getFullYear()} SupportAI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
