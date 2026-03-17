'use client';

import { useState, useEffect } from 'react';
import {
  Settings,
  Save,
  Building2,
  Bell,
  Link,
  Globe,
  Mail,
  MessageCircle,
  Hash,
  Check,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

interface TenantSettings {
  name: string;
  domain: string;
  logo_url: string;
  support_email: string;
  timezone: string;
  integrations: {
    slack: { enabled: boolean; webhook_url: string };
    email: { enabled: boolean; smtp_host: string; smtp_port: string };
    teams: { enabled: boolean; webhook_url: string };
  };
  notifications: {
    email_new_ticket: boolean;
    email_ticket_update: boolean;
    slack_new_ticket: boolean;
    slack_escalation: boolean;
    browser_push: boolean;
  };
}

const defaultSettings: TenantSettings = {
  name: 'Acme Support',
  domain: 'support.acme.com',
  logo_url: '',
  support_email: 'support@acme.com',
  timezone: 'America/New_York',
  integrations: {
    slack: { enabled: true, webhook_url: 'https://hooks.slack.com/services/...' },
    email: { enabled: true, smtp_host: 'smtp.acme.com', smtp_port: '587' },
    teams: { enabled: false, webhook_url: '' },
  },
  notifications: {
    email_new_ticket: true,
    email_ticket_update: true,
    slack_new_ticket: true,
    slack_escalation: true,
    browser_push: false,
  },
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<TenantSettings>(defaultSettings);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setTimeout(() => {
      setSettings(defaultSettings);
      setIsLoading(false);
    }, 500);
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast.success('Settings saved successfully');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleNotification = (key: keyof TenantSettings['notifications']) => {
    setSettings((prev) => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: !prev.notifications[key],
      },
    }));
  };

  const toggleIntegration = (key: keyof TenantSettings['integrations']) => {
    setSettings((prev) => ({
      ...prev,
      integrations: {
        ...prev.integrations,
        [key]: {
          ...prev.integrations[key],
          enabled: !prev.integrations[key].enabled,
        },
      },
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  const integrationCards = [
    {
      key: 'slack' as const,
      name: 'Slack',
      description: 'Send notifications and receive messages via Slack',
      icon: Hash,
      color: 'text-green-500 bg-green-50 dark:bg-green-900/20',
      fields: [
        {
          label: 'Webhook URL',
          value: settings.integrations.slack.webhook_url,
          key: 'webhook_url',
        },
      ],
    },
    {
      key: 'email' as const,
      name: 'Email',
      description: 'Configure SMTP settings for email support',
      icon: Mail,
      color: 'text-primary-500 bg-primary-50 dark:bg-primary-900/20',
      fields: [
        {
          label: 'SMTP Host',
          value: settings.integrations.email.smtp_host,
          key: 'smtp_host',
        },
        {
          label: 'SMTP Port',
          value: settings.integrations.email.smtp_port,
          key: 'smtp_port',
        },
      ],
    },
    {
      key: 'teams' as const,
      name: 'Microsoft Teams',
      description: 'Integrate with Microsoft Teams for notifications',
      icon: MessageCircle,
      color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20',
      fields: [
        {
          label: 'Webhook URL',
          value: settings.integrations.teams.webhook_url,
          key: 'webhook_url',
        },
      ],
    },
  ];

  const notificationOptions = [
    {
      key: 'email_new_ticket' as const,
      label: 'Email on new ticket',
      description: 'Send an email when a new ticket is created',
    },
    {
      key: 'email_ticket_update' as const,
      label: 'Email on ticket update',
      description: 'Send an email when a ticket is updated',
    },
    {
      key: 'slack_new_ticket' as const,
      label: 'Slack on new ticket',
      description: 'Post to Slack when a new ticket is created',
    },
    {
      key: 'slack_escalation' as const,
      label: 'Slack on escalation',
      description: 'Post to Slack when a ticket is escalated',
    },
    {
      key: 'browser_push' as const,
      label: 'Browser push notifications',
      description: 'Send push notifications to agents\' browsers',
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            Settings
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Configure your workspace and integration settings
          </p>
        </div>
        <Button
          onClick={handleSave}
          isLoading={isSaving}
          leftIcon={<Save className="w-4 h-4" />}
        >
          Save Changes
        </Button>
      </div>

      <div className="space-y-6">
        {/* General Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                General
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Organization Name"
                value={settings.name}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Your organization name"
              />
              <Input
                label="Support Domain"
                value={settings.domain}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, domain: e.target.value }))
                }
                placeholder="support.example.com"
              />
              <Input
                label="Support Email"
                type="email"
                value={settings.support_email}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    support_email: e.target.value,
                  }))
                }
                placeholder="support@example.com"
              />
              <Input
                label="Logo URL"
                value={settings.logo_url}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    logo_url: e.target.value,
                  }))
                }
                placeholder="https://example.com/logo.png"
              />
            </div>
          </CardContent>
        </Card>

        {/* Integrations */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Link className="w-5 h-5 text-accent-500" />
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                Integrations
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {integrationCards.map((integration) => {
              const Icon = integration.icon;
              const isEnabled = settings.integrations[integration.key].enabled;
              return (
                <div
                  key={integration.key}
                  className={cn(
                    'p-4 border rounded-xl transition-colors',
                    isEnabled
                      ? 'border-neutral-200 dark:border-neutral-700'
                      : 'border-neutral-100 dark:border-neutral-800 opacity-60'
                  )}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'w-10 h-10 rounded-lg flex items-center justify-center',
                          integration.color
                        )}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-neutral-900 dark:text-white">
                            {integration.name}
                          </p>
                          <Badge
                            variant={isEnabled ? 'green' : 'gray'}
                            size="sm"
                          >
                            {isEnabled ? 'Connected' : 'Disabled'}
                          </Badge>
                        </div>
                        <p className="text-xs text-neutral-500 mt-0.5">
                          {integration.description}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => toggleIntegration(integration.key)}
                      className={cn(
                        'relative w-11 h-6 rounded-full transition-colors',
                        isEnabled
                          ? 'bg-primary-500'
                          : 'bg-neutral-300 dark:bg-neutral-600'
                      )}
                    >
                      <div
                        className={cn(
                          'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform',
                          isEnabled ? 'translate-x-5' : 'translate-x-0'
                        )}
                      />
                    </button>
                  </div>
                  {isEnabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
                      {integration.fields.map((field) => (
                        <Input
                          key={field.key}
                          label={field.label}
                          value={field.value}
                          onChange={(e) =>
                            setSettings((prev) => ({
                              ...prev,
                              integrations: {
                                ...prev.integrations,
                                [integration.key]: {
                                  ...prev.integrations[integration.key],
                                  [field.key]: e.target.value,
                                },
                              },
                            }))
                          }
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-warning-500" />
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                Notification Preferences
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            {notificationOptions.map((option) => (
              <div
                key={option.key}
                className="flex items-center justify-between py-3 border-b border-neutral-100 dark:border-neutral-800 last:border-0"
              >
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    {option.label}
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    {option.description}
                  </p>
                </div>
                <button
                  onClick={() => toggleNotification(option.key)}
                  className={cn(
                    'relative w-11 h-6 rounded-full transition-colors',
                    settings.notifications[option.key]
                      ? 'bg-primary-500'
                      : 'bg-neutral-300 dark:bg-neutral-600'
                  )}
                >
                  <div
                    className={cn(
                      'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform',
                      settings.notifications[option.key]
                        ? 'translate-x-5'
                        : 'translate-x-0'
                    )}
                  />
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
