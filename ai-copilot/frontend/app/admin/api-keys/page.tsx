'use client';

import { useState, useEffect } from 'react';
import {
  Key,
  Plus,
  Copy,
  Check,
  Trash2,
  Eye,
  EyeOff,
  Shield,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { cn, formatDate } from '@/lib/utils';
import * as adminService from '@/services/admin';
import toast from 'react-hot-toast';
import type { ApiKeyInfo } from '@/types';

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => {
    loadKeys();
  }, []);

  const loadKeys = async () => {
    try {
      const data = await adminService.getAPIKeys();
      setKeys(data.items || []);
    } catch {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setIsCreating(true);
    try {
      const result = await adminService.createAPIKey({ name: newKeyName });
      setNewlyCreatedKey(result.key || result.id);
      setKeys((prev) => [result, ...prev]);
      setNewKeyName('');
      toast.success('API key created');
    } catch {
      toast.error('Failed to create API key');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (keyId: string) => {
    try {
      await adminService.deleteAPIKey(keyId);
      setKeys((prev) => prev.filter((k) => k.id !== keyId));
      setConfirmDelete(null);
      toast.success('API key revoked');
    } catch {
      toast.error('Failed to revoke API key');
    }
  };

  const handleCopy = (text: string, keyId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
    toast.success('Copied to clipboard');
  };

  const toggleReveal = (keyId: string) => {
    setRevealedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(keyId)) {
        next.delete(keyId);
      } else {
        next.add(keyId);
      }
      return next;
    });
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return '••••••••';
    return key.slice(0, 4) + '••••••••••••' + key.slice(-4);
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            API Keys
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage API keys for external integrations
          </p>
        </div>
        <Button
          onClick={() => {
            setShowCreate(true);
            setNewlyCreatedKey(null);
          }}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Create API Key
        </Button>
      </div>

      {/* Security Notice */}
      <Card className="mb-6 border-warning-200 dark:border-warning-800">
        <CardContent className="py-3">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-warning-500 shrink-0" />
            <p className="text-sm text-warning-700 dark:text-warning-400">
              API keys grant access to your account. Keep them secret and rotate
              them regularly. Never share keys in public repositories.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Keys List */}
      {keys.length === 0 ? (
        <EmptyState
          icon={<Key className="w-8 h-8" />}
          title="No API keys"
          description="Create an API key to integrate with external services."
          actionLabel="Create API Key"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="space-y-3">
          {keys.map((apiKey) => (
            <Card key={apiKey.id}>
              <CardContent className="py-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center shrink-0">
                    <Key className="w-5 h-5 text-neutral-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-sm font-semibold text-neutral-900 dark:text-white">
                        {apiKey.name}
                      </p>
                      <Badge
                        variant={apiKey.is_active !== false ? 'green' : 'red'}
                        size="sm"
                      >
                        {apiKey.is_active !== false ? 'Active' : 'Revoked'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="text-xs text-neutral-500 font-mono">
                        {revealedKeys.has(apiKey.id) && apiKey.key
                          ? apiKey.key
                          : maskKey(apiKey.key || apiKey.prefix || 'sk-')}
                      </code>
                      {apiKey.key && (
                        <button
                          onClick={() => toggleReveal(apiKey.id)}
                          className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                        >
                          {revealedKeys.has(apiKey.id) ? (
                            <EyeOff className="w-3.5 h-3.5" />
                          ) : (
                            <Eye className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                    </div>
                    <p className="text-[11px] text-neutral-400 mt-1">
                      Created {apiKey.created_at ? formatDate(apiKey.created_at) : 'unknown'}{' '}
                      {apiKey.last_used_at &&
                        ` · Last used ${formatDate(apiKey.last_used_at)}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleCopy(apiKey.key || apiKey.prefix || '', apiKey.id)
                      }
                    >
                      {copiedKey === apiKey.id ? (
                        <Check className="w-4 h-4 text-accent-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmDelete(apiKey.id)}
                      className="text-error-500 hover:text-error-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Key Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => {
          setShowCreate(false);
          setNewlyCreatedKey(null);
        }}
        title="Create API Key"
        actions={
          !newlyCreatedKey ? (
            <>
              <Button variant="outline" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                isLoading={isCreating}
                disabled={!newKeyName.trim()}
              >
                Create Key
              </Button>
            </>
          ) : (
            <Button
              onClick={() => {
                setShowCreate(false);
                setNewlyCreatedKey(null);
              }}
            >
              Done
            </Button>
          )
        }
      >
        {!newlyCreatedKey ? (
          <Input
            label="Key Name"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="e.g., Production API, Slack Integration"
            helperText="A descriptive name to identify this API key"
          />
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-accent-50 dark:bg-accent-900/20 border border-accent-200 dark:border-accent-800 rounded-xl">
              <p className="text-sm font-medium text-accent-700 dark:text-accent-400 mb-2">
                Your new API key (copy it now - it won&apos;t be shown again):
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm font-mono text-neutral-900 dark:text-white bg-white dark:bg-neutral-800 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 break-all">
                  {newlyCreatedKey}
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(newlyCreatedKey, 'new')}
                >
                  {copiedKey === 'new' ? (
                    <Check className="w-4 h-4 text-accent-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            <p className="text-xs text-warning-600 dark:text-warning-400">
              Store this key in a secure location. For security reasons, you
              won&apos;t be able to view it again.
            </p>
          </div>
        )}
      </Modal>

      {/* Confirm Delete Modal */}
      <Modal
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        title="Revoke API Key"
        actions={
          <>
            <Button variant="outline" onClick={() => setConfirmDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => confirmDelete && handleDelete(confirmDelete)}
            >
              Revoke Key
            </Button>
          </>
        }
      >
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Are you sure you want to revoke this API key? Any integrations using
          this key will immediately lose access. This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
