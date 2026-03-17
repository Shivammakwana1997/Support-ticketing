'use client';

import { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { AgentList } from '@/components/admin/AgentList';
import * as adminService from '@/services/admin';
import toast from 'react-hot-toast';
import type { Agent } from '@/types/user';

export default function AgentManagementPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await adminService.getAgents();
      setAgents(data.items || []);
    } catch {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async (agent: Agent) => {
    try {
      const updated = await adminService.updateAgent(agent.id, {
        is_active: !agent.is_active,
      });
      setAgents((prev) =>
        prev.map((a) => (a.id === agent.id ? { ...a, ...updated } : a))
      );
      toast.success(
        `Agent ${updated.is_active ? 'activated' : 'deactivated'}`
      );
    } catch {
      toast.error('Failed to update agent status');
    }
  };

  const handleEdit = (agent: Agent) => {
    // In a real app, this would open an edit modal
    toast.success(`Editing ${agent.name}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
          Agent Management
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Manage your support team and agent configurations
        </p>
      </div>

      {agents.length === 0 ? (
        <EmptyState
          icon={<Users className="w-8 h-8" />}
          title="No agents configured"
          description="Add agents to your support team to get started."
        />
      ) : (
        <AgentList
          agents={agents}
          onToggle={handleToggleStatus}
          onEdit={handleEdit}
        />
      )}
    </div>
  );
}
