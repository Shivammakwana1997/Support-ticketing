'use client';

import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { Star, MessageSquare, Clock } from 'lucide-react';
import { formatDuration } from '@/lib/utils';
import type { Agent } from '@/types/user';

interface AgentListProps {
  agents: Agent[];
  onToggleStatus?: (agentId: string, status: 'available' | 'offline') => void;
  onEditSkills?: (agent: Agent) => void;
}

const statusVariant: Record<string, 'green' | 'yellow' | 'gray'> = {
  available: 'green',
  busy: 'yellow',
  offline: 'gray',
};

export function AgentList({ agents, onToggleStatus, onEditSkills }: AgentListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agents.map((agent) => (
        <Card key={agent.id} className="overflow-hidden">
          <CardContent className="pt-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <Avatar
                  name={agent.user?.name || 'Agent'}
                  size="lg"
                  status={agent.status === 'available' ? 'online' : agent.status === 'busy' ? 'busy' : 'offline'}
                />
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-white">
                    {agent.user?.name || 'Unknown Agent'}
                  </h3>
                  <p className="text-xs text-neutral-500">{agent.user?.email}</p>
                </div>
              </div>
              <Badge variant={statusVariant[agent.status] || 'gray'} dot>
                {agent.status}
              </Badge>
            </div>

            {/* Skills */}
            {agent.skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {agent.skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3 py-3 border-t border-neutral-200 dark:border-neutral-700">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-xs text-neutral-500 mb-0.5">
                  <MessageSquare className="w-3 h-3" />
                  Active
                </div>
                <p className="text-sm font-semibold text-neutral-900 dark:text-white">
                  {agent.active_conversations_count}
                </p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-xs text-neutral-500 mb-0.5">
                  <Star className="w-3 h-3" />
                  Rating
                </div>
                <p className="text-sm font-semibold text-neutral-900 dark:text-white">
                  {agent.average_rating?.toFixed(1) || '-'}
                </p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-xs text-neutral-500 mb-0.5">
                  <Clock className="w-3 h-3" />
                  Resolved
                </div>
                <p className="text-sm font-semibold text-neutral-900 dark:text-white">
                  {agent.total_resolved}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-3 border-t border-neutral-200 dark:border-neutral-700">
              {onToggleStatus && (
                <button
                  onClick={() =>
                    onToggleStatus(
                      agent.id,
                      agent.status === 'available' ? 'offline' : 'available'
                    )
                  }
                  className="flex-1 py-2 text-xs font-medium text-center rounded-lg border border-neutral-200 dark:border-neutral-600 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                >
                  {agent.status === 'available' ? 'Set Offline' : 'Set Available'}
                </button>
              )}
              {onEditSkills && (
                <button
                  onClick={() => onEditSkills(agent)}
                  className="flex-1 py-2 text-xs font-medium text-center rounded-lg bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
                >
                  Edit Skills
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
