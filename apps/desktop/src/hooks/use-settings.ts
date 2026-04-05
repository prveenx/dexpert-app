import { useState, useEffect, useCallback } from 'react';
import { ApiClient } from '../lib/api-client';
import type { EngineSettings } from '@dexpert/types';

export function useSettings() {
  const [settings, setSettings] = useState<EngineSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await ApiClient.getInstance().get<EngineSettings>('/settings');
      setSettings(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch settings'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateSettings = useCallback(async (updates: Partial<EngineSettings>) => {
    setIsLoading(true);
    try {
      const data = await ApiClient.getInstance().patch<EngineSettings>('/settings', updates);
      setSettings(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to update settings'));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return {
    settings,
    isLoading,
    error,
    refresh: fetchSettings,
    updateSettings,
  };
}
