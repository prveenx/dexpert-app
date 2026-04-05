// ── Settings View (v2 Expanded) ────────────────────────
// Professional, future-proof configuration panel for Dexpert.
// Categories: Intelligence, Appearance, Workspace, Security, Advanced.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { 
  Settings2, Brain, Cpu, Globe, Database, 
  Key, Palette, Shield, Info, Save, ChevronRight,
  Sparkles, Terminal, Activity, Monitor, Eye, 
  Lock, Zap, Gauge, Languages, Code2, Layers
} from 'lucide-react';
import { useSettings } from '../../hooks/use-settings';

type Section = 'intelligence' | 'appearance' | 'workspace' | 'security' | 'advanced';

export function SettingsView() {
  const { settings, updateSettings } = useSettings();
  const [activeSection, setActiveSection] = useState<Section>('intelligence');

  const navItems = [
    { id: 'intelligence', icon: Brain, label: 'Intelligence Core', color: 'text-violet-500' },
    { id: 'appearance', icon: Palette, label: 'Visual Interface', color: 'text-rose-500' },
    { id: 'workspace', icon: Monitor, label: 'IDE Workspace', color: 'text-sky-500' },
    { id: 'security', icon: Shield, label: 'Privacy & Keys', color: 'text-emerald-500' },
    { id: 'advanced', icon: Zap, label: 'Advanced Engine', color: 'text-amber-500' },
  ];

  return (
    <div className="flex-1 flex bg-white dark:bg-zinc-950/40 backdrop-blur-3xl animate-in fade-in duration-700 overflow-hidden select-none">
      {/* Settings Navigation Sidebar */}
      <div className="w-80 border-r border-zinc-200 dark:border-zinc-800/60 p-8 flex flex-col gap-8 bg-zinc-50/20 dark:bg-zinc-900/10">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-violet-600 rounded-[22px] shadow-2xl shadow-violet-900/40 transform rotate-3">
            <Settings2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-black text-zinc-900 dark:text-zinc-50 uppercase tracking-[0.2em]">Dexpert v2</h2>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest opacity-60">Control Center / Node-01</p>
          </div>
        </div>

        <nav className="flex flex-col gap-3">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id as Section)}
              className={`group flex items-center gap-4 px-5 py-4 rounded-[22px] text-[13px] font-black transition-all duration-300 relative
                ${activeSection === item.id 
                  ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-50 shadow-xl dark:shadow-zinc-950/50 scale-105 border border-zinc-200 dark:border-zinc-800' 
                  : 'text-zinc-500 dark:text-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900/40'
                }`}
            >
              <item.icon className={`w-5 h-5 transition-transform duration-500 group-hover:scale-110 ${activeSection === item.id ? item.color : 'opacity-40'}`} />
              {item.label}
              {activeSection === item.id && (
                 <div className="absolute left-0 w-1.5 h-6 bg-violet-600 rounded-full -translate-x-1/2" />
              )}
              {activeSection === item.id && <ChevronRight className="w-4 h-4 ml-auto opacity-40 shrink-0" />}
            </button>
          ))}
        </nav>

        <div className="mt-auto p-6 rounded-[32px] bg-zinc-100 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800/80">
           <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.15em]">Core Online</span>
           </div>
           <p className="text-[10px] text-zinc-400 dark:text-zinc-600 leading-relaxed font-bold italic uppercase tracking-tight">System synchronizing via Rust-bridge WebSocket at 48765/tcp.</p>
        </div>
      </div>

      {/* Main Settings Content Area */}
      <main className="flex-1 overflow-y-auto p-16 px-24 custom-scrollbar scroll-smooth">
        <div className="max-w-4xl mx-auto pb-48">
          
          {/* ── Intelligence Section ─────────────────────── */}
          {activeSection === 'intelligence' && (
            <div className="space-y-12 animate-in slide-in-from-bottom-8 duration-700">
              <SectionHeader 
                title="Intelligence Core" 
                desc="Orchestrate the neural distribution across specialist agents." 
                icon={Brain} 
              />
              
              <div className="grid grid-cols-1 gap-8">
                 <ConfigCard 
                    title="System Orchestrator" 
                    subtitle="Planning & High-Level Reasoning" 
                    icon={Sparkles}
                    accent="violet"
                 >
                    <div className="grid grid-cols-2 gap-6">
                       <ControlField label="Neural Engine">
                          <select className="v2-select">
                             <option>Gemini 1.5 Pro</option>
                             <option>Claude 3.5 Sonnet</option>
                             <option>GPT-4o</option>
                          </select>
                       </ControlField>
                       <ControlField label="Creativity Index (Temp)">
                          <input type="range" className="v2-range-violet" />
                       </ControlField>
                    </div>
                 </ConfigCard>

                 <ConfigCard 
                    title="Environment Specialists" 
                    subtitle="OS Execution & Web Interaction" 
                    icon={Cpu}
                    accent="amber"
                 >
                    <div className="grid grid-cols-2 gap-6">
                       <ControlField label="Specialist Engine">
                          <select className="v2-select">
                             <option>Inherit Orchestrator</option>
                             <option>Gemini 1.5 Flash</option>
                             <option>GPT-4o Mini</option>
                          </select>
                       </ControlField>
                       <ControlField label="Self-Correction Loops">
                          <select className="v2-select">
                             <option>Extreme (5 Retries)</option>
                             <option>Balanced (3 Retries)</option>
                             <option>Direct (None)</option>
                          </select>
                       </ControlField>
                    </div>
                 </ConfigCard>
              </div>
            </div>
          )}

          {/* ── Appearance Section ──────────────────────── */}
          {activeSection === 'appearance' && (
            <div className="space-y-12 animate-in slide-in-from-bottom-8 duration-700">
              <SectionHeader 
                title="Visual Interface" 
                desc="Customize the aesthetic layer of your agentic environment." 
                icon={Palette} 
              />
              
              <ConfigCard title="Theme Engine" subtitle="Global Identity" icon={Eye} accent="rose">
                 <div className="grid grid-cols-4 gap-4">
                    <ThemeButton active label="Dark Mode" color="bg-zinc-950" />
                    <ThemeButton label="Light Mode" color="bg-white border" />
                    <ThemeButton label="OLED Black" color="bg-black" />
                    <ThemeButton label="Cyber Green" color="bg-zinc-900 border-emerald-500/20" />
                 </div>
              </ConfigCard>

              <ConfigCard title="Typography & Density" subtitle="Legibility Control" icon={Languages} accent="sky">
                 <div className="grid grid-cols-2 gap-8">
                    <ControlField label="Main Font Family">
                       <select className="v2-select">
                          <option>Inter (Modern Sans)</option>
                          <option>Roboto (Standard)</option>
                          <option>JetBrains Mono</option>
                       </select>
                    </ControlField>
                    <ControlField label="Visual Density">
                       <div className="flex gap-2">
                          <button className="flex-1 py-3 bg-zinc-100 dark:bg-zinc-900 rounded-xl text-[10px] font-black tracking-widest text-zinc-500">COZY</button>
                          <button className="flex-1 py-3 bg-violet-600 text-white rounded-xl text-[10px] font-black tracking-widest">COMPACT</button>
                       </div>
                    </ControlField>
                 </div>
              </ConfigCard>
            </div>
          )}

          {/* ── Workspace Section ───────────────────────── */}
          {activeSection === 'workspace' && (
            <div className="space-y-12 animate-in slide-in-from-bottom-8 duration-700">
              <SectionHeader 
                title="IDE Workspace" 
                desc="Fine-tune how agents interact with your local file system." 
                icon={Monitor} 
              />
              
              <ConfigCard title="Runtime Environment" subtitle="Shell & Directory Settings" icon={Terminal} accent="sky">
                 <div className="space-y-6">
                    <ControlField label="System Default Shell">
                       <select className="v2-select">
                          <option>PowerShell Core (Windows)</option>
                          <option>Zsh / Bash (WSL)</option>
                          <option>Command Prompt</option>
                       </select>
                    </ControlField>
                    <ControlField label="Workspace Root Path">
                       <div className="flex gap-2">
                          <input type="text" value="C:\Users\user\Desktop\dexpert_desktop" className="v2-select flex-1 font-mono" readOnly />
                          <button className="px-6 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-2xl text-[10px] font-black uppercase tracking-widest">Update</button>
                       </div>
                    </ControlField>
                 </div>
              </ConfigCard>
            </div>
          )}

          {/* ── Security Section ────────────────────────── */}
          {activeSection === 'security' && (
            <div className="space-y-12 animate-in slide-in-from-bottom-8 duration-700">
              <SectionHeader 
                title="Privacy & Keys" 
                desc="Manage neural network identities and local encryption." 
                icon={Shield} 
              />
              
              <div className="space-y-6">
                 <KeyInput label="Google AI (Gemini) API Key" placeholder="••••••••••••••••" />
                 <KeyInput label="Anthropic (Claude) API Key" placeholder="••••••••••••••••" />
                 <KeyInput label="OpenAI (GPT) API Key" placeholder="••••••••••••••••" />
              </div>

              <ConfigCard title="Execution Safeguards" subtitle="Agent Permissions" icon={Lock} accent="emerald">
                 <div className="space-y-4">
                    <ToggleField label="Request approval for OS commands" active />
                    <ToggleField label="Request approval for File modifications" />
                    <ToggleField label="Local database encryption" active />
                 </div>
              </ConfigCard>
            </div>
          )}

          {/* ── Advanced Section ────────────────────────── */}
          {activeSection === 'advanced' && (
            <div className="space-y-12 animate-in slide-in-from-bottom-8 duration-700">
              <SectionHeader 
                title="Advanced Engine" 
                desc="Developer tools and experimental experimental features." 
                icon={Zap} 
              />
              
              <ConfigCard title="Experimental v2 Features" subtitle="Beta Access" icon={Layers} accent="amber">
                 <div className="space-y-4">
                    <ToggleField label="Enable Multi-Device Sandboxing" active />
                    <ToggleField label="Enable Self-Healing Context (Auto-Fix)" active />
                    <ToggleField label="Web Search v2 (Autonomous Browser)" />
                 </div>
              </ConfigCard>

              <div className="p-8 rounded-[40px] bg-red-500/5 border border-red-500/20">
                 <h4 className="text-red-500 text-xs font-black uppercase tracking-widest mb-2">Danger Zone</h4>
                 <p className="text-[10px] text-red-500/60 font-bold uppercase mb-6">Resetting configuration will wipe all API keys and session memory.</p>
                 <button className="px-8 py-3 bg-red-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-red-700 transition-all">Factory Reset Environment</button>
              </div>
            </div>
          )}

          {/* Global Synchronize Bar */}
          <div className="pt-16 mt-24 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
             <div>
                <p className="text-xs font-bold text-zinc-500">UNSAVED CHANGES DETECTED</p>
                <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">Configuration will be pushed to Node-01 engine.</p>
             </div>
             <button className="flex items-center gap-4 bg-violet-600 text-white px-10 py-5 rounded-[28px] text-[13px] font-black shadow-2xl shadow-violet-900/40 hover:scale-105 active:scale-95 transition-all">
                <Save className="w-5 h-5" /> SYNCHRONIZE ENVIRONMENT
             </button>
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Components Helper ───────────────────────────────

function SectionHeader({ title, desc, icon: Icon }: any) {
  return (
    <header className="mb-16">
      <div className="flex items-center gap-4 mb-4">
         <Icon className="w-8 h-8 text-zinc-800 dark:text-zinc-50 opacity-40" />
         <h1 className="text-4xl font-black text-zinc-900 dark:text-zinc-50 tracking-tighter">{title}</h1>
      </div>
      <p className="text-zinc-500 dark:text-zinc-400 text-lg font-bold leading-relaxed max-w-xl">{desc}</p>
    </header>
  );
}

function ConfigCard({ title, subtitle, icon: Icon, accent, children }: any) {
  const accentColor = accent === 'violet' ? 'bg-violet-600 text-white' : 
                      accent === 'amber' ? 'bg-amber-500 text-white' :
                      accent === 'rose' ? 'bg-rose-500 text-white' :
                      accent === 'sky' ? 'bg-sky-500 text-white' :
                      accent === 'emerald' ? 'bg-emerald-500 text-white' : 'bg-zinc-500 text-white';

  return (
    <div className="p-10 rounded-[48px] bg-zinc-50 dark:bg-zinc-900/40 border border-zinc-200 dark:border-zinc-800/80 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors group">
      <div className="flex items-center gap-6 mb-10">
        <div className={`p-4 rounded-[28px] shadow-2xl transition-transform duration-500 group-hover:scale-110 group-hover:rotate-6 ${accentColor}`}>
          <Icon className="w-7 h-7" />
        </div>
        <div>
          <h3 className="text-xl font-black text-zinc-900 dark:text-zinc-50 tracking-tight">{title}</h3>
          <p className="text-xs text-zinc-500 font-bold uppercase tracking-[0.14em] opacity-80">{subtitle}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function ControlField({ label, children }: any) {
  return (
    <div className="space-y-3 flex-1">
      <label className="text-[10px] font-black text-zinc-400 dark:text-zinc-600 uppercase tracking-widest px-2">{label}</label>
      {children}
    </div>
  );
}

function ToggleField({ label, active = false }: any) {
  return (
    <div className="flex items-center justify-between p-5 rounded-3xl bg-zinc-100 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 transition-all cursor-pointer">
      <span className="text-xs font-black text-zinc-700 dark:text-zinc-300 uppercase tracking-tight">{label}</span>
      <div className={`w-12 h-6 rounded-full relative transition-colors ${active ? 'bg-emerald-500' : 'bg-zinc-300 dark:bg-zinc-800'}`}>
        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${active ? 'left-7 shadow-lg' : 'left-1'}`} />
      </div>
    </div>
  );
}

function KeyInput({ label, placeholder }: any) {
  return (
    <div className="p-8 rounded-[40px] bg-zinc-50 dark:bg-zinc-900/40 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between group">
       <div className="flex flex-col gap-2">
          <label className="text-[10px] font-black text-zinc-400 dark:text-zinc-600 uppercase tracking-widest">{label}</label>
          <input 
             type="password" 
             placeholder={placeholder} 
             className="bg-transparent text-xl font-black text-zinc-400 dark:text-zinc-800 outline-none w-64 tracking-[0.3em] font-serif" 
          />
       </div>
       <button className="px-6 py-3 bg-zinc-100 dark:bg-zinc-800 rounded-[20px] text-[10px] font-black text-zinc-500 uppercase tracking-widest hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all opacity-0 group-hover:opacity-100">Update API Key</button>
    </div>
  );
}

function ThemeButton({ label, color, active = false }: any) {
  return (
    <button className={`flex flex-col items-center gap-3 p-4 rounded-3xl border-2 transition-all ${active ? 'border-violet-600 shadow-xl' : 'border-transparent hover:bg-zinc-100 dark:hover:bg-zinc-900'}`}>
       <div className={`w-16 h-12 rounded-2xl ${color}`} />
       <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">{label}</span>
    </button>
  );
}