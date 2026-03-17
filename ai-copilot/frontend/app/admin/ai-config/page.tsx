'use client';

import { useState, useEffect } from 'react';
import {
  Cpu,
  Save,
  RotateCcw,
  Sliders,
  BookOpen,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Spinner } from '@/components/ui/Spinner';
import * as adminService from '@/services/admin';
import toast from 'react-hot-toast';
import type { AIConfig } from '@/types';

const defaultConfig: AIConfig = {
  model: 'gpt-4',
  temperature: 0.7,
  max_tokens: 1024,
  system_prompt: 'You are a helpful customer support assistant.',
  rag_enabled: true,
  rag_top_k: 5,
  rag_similarity_threshold: 0.75,
  auto_respond: false,
  auto_respond_confidence: 0.9,
};

export default function AIConfigPage() {
  const [config, setConfig] = useState<AIConfig>(defaultConfig);
  const [originalConfig, setOriginalConfig] = useState<AIConfig>(defaultConfig);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await adminService.getAIConfig();
      setConfig(data);
      setOriginalConfig(data);
    } catch {
      // Use defaults
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await adminService.updateAIConfig(config);
      setConfig(updated);
      setOriginalConfig(updated);
      toast.success('AI configuration saved');
    } catch {
      toast.error('Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(originalConfig);
  };

  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);

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
            AI Configuration
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Configure the AI model, RAG settings, and auto-response behavior
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges}
            leftIcon={<RotateCcw className="w-4 h-4" />}
          >
            Reset
          </Button>
          <Button
            onClick={handleSave}
            isLoading={isSaving}
            disabled={!hasChanges}
            leftIcon={<Save className="w-4 h-4" />}
          >
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary-500" />
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                Model Settings
              </h2>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <Select
              label="Model"
              value={config.model}
              onChange={(e) =>
                setConfig((prev) => ({ ...prev, model: e.target.value }))
              }
              options={[
                { value: 'gpt-4', label: 'GPT-4' },
                { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
                { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                { value: 'claude-3-opus', label: 'Claude 3 Opus' },
                { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
              ]}
            />

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Temperature: {config.temperature.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.01"
                value={config.temperature}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    temperature: parseFloat(e.target.value),
                  }))
                }
                className="w-full h-2 bg-neutral-200 dark:bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
              />
              <div className="flex justify-between text-xs text-neutral-400 mt-1">
                <span>Precise (0)</span>
                <span>Creative (2)</span>
              </div>
            </div>

            <Input
              label="Max Tokens"
              type="number"
              value={config.max_tokens.toString()}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  max_tokens: parseInt(e.target.value) || 0,
                }))
              }
              helperText="Maximum number of tokens in AI response"
            />

            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                System Prompt
              </label>
              <textarea
                value={config.system_prompt}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    system_prompt: e.target.value,
                  }))
                }
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 input-focus resize-none"
                placeholder="System prompt for the AI model..."
              />
            </div>
          </CardContent>
        </Card>

        {/* RAG Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-accent-500" />
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  RAG Settings
                </h2>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    Enable RAG
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Retrieve relevant knowledge base articles for context
                  </p>
                </div>
                <button
                  onClick={() =>
                    setConfig((prev) => ({
                      ...prev,
                      rag_enabled: !prev.rag_enabled,
                    }))
                  }
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    config.rag_enabled
                      ? 'bg-primary-500'
                      : 'bg-neutral-300 dark:bg-neutral-600'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                      config.rag_enabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {config.rag_enabled && (
                <>
                  <Input
                    label="Top K Results"
                    type="number"
                    value={config.rag_top_k.toString()}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        rag_top_k: parseInt(e.target.value) || 1,
                      }))
                    }
                    helperText="Number of relevant chunks to retrieve"
                  />

                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      Similarity Threshold:{' '}
                      {config.rag_similarity_threshold.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={config.rag_similarity_threshold}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          rag_similarity_threshold: parseFloat(e.target.value),
                        }))
                      }
                      className="w-full h-2 bg-neutral-200 dark:bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-accent-500"
                    />
                    <div className="flex justify-between text-xs text-neutral-400 mt-1">
                      <span>Broad (0)</span>
                      <span>Strict (1)</span>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Auto-Response Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-warning-500" />
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                  Auto-Response
                </h2>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    Enable Auto-Response
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Automatically respond to high-confidence queries
                  </p>
                </div>
                <button
                  onClick={() =>
                    setConfig((prev) => ({
                      ...prev,
                      auto_respond: !prev.auto_respond,
                    }))
                  }
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    config.auto_respond
                      ? 'bg-primary-500'
                      : 'bg-neutral-300 dark:bg-neutral-600'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                      config.auto_respond ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {config.auto_respond && (
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                    Confidence Threshold:{' '}
                    {(config.auto_respond_confidence * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1"
                    step="0.01"
                    value={config.auto_respond_confidence}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        auto_respond_confidence: parseFloat(e.target.value),
                      }))
                    }
                    className="w-full h-2 bg-neutral-200 dark:bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-warning-500"
                  />
                  <div className="flex justify-between text-xs text-neutral-400 mt-1">
                    <span>50% (More responses)</span>
                    <span>100% (Fewer, safer)</span>
                  </div>
                  <p className="text-xs text-warning-600 dark:text-warning-400 mt-2">
                    Only queries above this confidence will get automatic responses.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
