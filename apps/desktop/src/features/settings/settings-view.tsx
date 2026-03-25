// FILE: apps/desktop/src/features/settings/settings-view.tsx
import React, { useState, useEffect } from 'react';
import { Key, Bot, Settings as SettingsIcon, Save, ShieldCheck, Loader2, Sparkles, Cpu } from 'lucide-react';
import { ENGINE_DEFAULT_PORT } from '../../lib/constants';

export function SettingsView() {
  const [activeTab, setActiveTab] = useState<'api_keys' | 'models' | 'general'>('api_keys');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Form State
  const[keys, setKeys] = useState({ google: '', openai: '', anthropic: '', groq: '' });
  const[defaultModel, setDefaultModel] = useState('gemini/gemini-3.1-flash-lite-preview');
  const [globalOverride, setGlobalOverride] = useState('');

  useEffect(() => {
    fetch(`http://127.0.0.1:${ENGINE_DEFAULT_PORT}/api/settings`)
      .then(res => res.json())
      .then(data => {
        setKeys({
          google: data.apiKeys?.hasGoogle ? '********' : '',
          openai: data.apiKeys?.hasOpenAI ? '********' : '',
          anthropic: data.apiKeys?.hasAnthropic ? '********' : '',
          groq: data.apiKeys?.hasGroq ? '********' : '',
        });
        if (data.defaultModel) setDefaultModel(data.defaultModel);
        if (data.globalModelOverride) setGlobalOverride(data.globalModelOverride);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load settings:", err);
        setLoading(false);
      });
  },[]);

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage('');

    const payload: any = { apiKeys: {} };
    
    // Only send keys that have been modified (aren't asterisks)
    if (keys.google && keys.google !== '********') payload.apiKeys.google = keys.google;
    if (keys.openai && keys.openai !== '********') payload.apiKeys.openai = keys.openai;
    if (keys.anthropic && keys.anthropic !== '********') payload.apiKeys.anthropic = keys.anthropic;
    if (keys.groq && keys.groq !== '********') payload.apiKeys.groq = keys.groq;

    if (defaultModel) payload.defaultModel = defaultModel;
    payload.globalModelOverride = globalOverride;

    try {
      await fetch(`http://127.0.0.1:${ENGINE_DEFAULT_PORT}/api/settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      setKeys(prev => ({
        google: prev.google ? '********' : '',
        openai: prev.openai ? '********' : '',
        anthropic: prev.anthropic ? '********' : '',
        groq: prev.groq ? '********' : '',
      }));
      
      setSaveMessage('Settings saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (err) {
      setSaveMessage('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex-1 flex items-center justify-center bg-white dark:bg-zinc-950"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-950 animate-in fade-in duration-500">
      <div className="flex-shrink-0 px-8 py-6 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Settings</h1>
            <p className="text-zinc-500 text-sm mt-1">Configure Dexpert engines, providers, and API keys.</p>
          </div>
          <button 
            onClick={handleSave}
            disabled={saving}
            className="bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-violet-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Changes
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-6 mt-8 border-b border-zinc-200 dark:border-zinc-800">
          <button onClick={() => setActiveTab('api_keys')} className={`pb-3 text-sm font-bold border-b-2 transition-all ${activeTab === 'api_keys' ? 'border-violet-500 text-violet-600 dark:text-violet-400' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}>
            <span className="flex items-center gap-2"><Key className="w-4 h-4" /> API Keys</span>
          </button>
          <button onClick={() => setActiveTab('models')} className={`pb-3 text-sm font-bold border-b-2 transition-all ${activeTab === 'models' ? 'border-violet-500 text-violet-600 dark:text-violet-400' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}>
            <span className="flex items-center gap-2"><Sparkles className="w-4 h-4" /> Models</span>
          </button>
          <button onClick={() => setActiveTab('general')} className={`pb-3 text-sm font-bold border-b-2 transition-all ${activeTab === 'general' ? 'border-violet-500 text-violet-600 dark:text-violet-400' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}>
            <span className="flex items-center gap-2"><SettingsIcon className="w-4 h-4" /> General</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8 bg-zinc-50/50 dark:bg-zinc-900/20 custom-scrollbar">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {saveMessage && (
            <div className="p-3 mb-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm font-medium flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" /> {saveMessage}
            </div>
          )}

          {activeTab === 'api_keys' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-1">Provider Credentials</h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-6">Keys are stored securely in your local AppData directory.</p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">Google Gemini API Key</label>
                    <input 
                      type="password" 
                      value={keys.google} 
                      onChange={(e) => setKeys({...keys, google: e.target.value})}
                      placeholder="AIzaSy..." 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">OpenAI API Key</label>
                    <input 
                      type="password" 
                      value={keys.openai} 
                      onChange={(e) => setKeys({...keys, openai: e.target.value})}
                      placeholder="sk-proj-..." 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">Anthropic API Key</label>
                    <input 
                      type="password" 
                      value={keys.anthropic} 
                      onChange={(e) => setKeys({...keys, anthropic: e.target.value})}
                      placeholder="sk-ant-..." 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">Groq API Key (Fast Inference)</label>
                    <input 
                      type="password" 
                      value={keys.groq} 
                      onChange={(e) => setKeys({...keys, groq: e.target.value})}
                      placeholder="gsk_..." 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all font-mono text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'models' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-violet-100 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400 rounded-xl flex items-center justify-center">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">LLM Configuration</h2>
                    <p className="text-xs text-zinc-500">Configure default routing and global overrides.</p>
                  </div>
                </div>

                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">Default Fallback Model</label>
                    <input 
                      type="text" 
                      value={defaultModel} 
                      onChange={(e) => setDefaultModel(e.target.value)}
                      placeholder="e.g. gemini/gemini-3.1-flash-lite-preview" 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 transition-all font-mono text-sm"
                    />
                    <p className="text-[11px] text-zinc-500 mt-1">Provider prefix required for LiteLLM (e.g., openai/gpt-4o, anthropic/claude-3-5-sonnet).</p>
                  </div>
                  
                  <div className="pt-2">
                    <label className="block text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">Global Override Model</label>
                    <input 
                      type="text" 
                      value={globalOverride} 
                      onChange={(e) => setGlobalOverride(e.target.value)}
                      placeholder="Optional override..." 
                      className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2.5 outline-none focus:border-violet-500/50 transition-all font-mono text-sm"
                    />
                    <p className="text-[11px] text-amber-600 dark:text-amber-500/80 mt-1 font-medium">Warning: This forces all agents (Planner, Browser, OS) to use this specific model, overriding their individual configs.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'general' && (
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4">Application Behavior</h2>
              <div className="flex items-center justify-between p-4 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl">
                <div>
                  <p className="font-semibold text-sm">Engine Status</p>
                  <p className="text-xs text-zinc-500 mt-0.5">Dexpert Agent Runtime is online.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-lg text-xs font-bold">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Connected
                </div>
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}