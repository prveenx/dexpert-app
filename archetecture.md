dexpert/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── deploy-web.yml
│
├── apps/
│   ├── desktop/
│   ├── web/
│   └── cli/
│
├── engine/
│
├── packages/
│   ├── ui/
│   ├── types/
│   └── config/
│
├── native/
│   └── dexpert-core/
│
├── package.json                     pnpm workspace root
├── pnpm-workspace.yaml
├── turbo.json
├── tsconfig.base.json
├── .env.example
└── .gitignore


════════════════════════════════════════════════════════════
 packages/ui/                        @dexpert/ui
 The design system. Primitive + compound components.
 Zero business logic. Zero API calls. Zero Electron coupling.
 Consumed by: apps/desktop renderer, apps/web, apps/cli
════════════════════════════════════════════════════════════

packages/ui/
├── src/
│   ├── index.ts                     re-exports everything
│   │
│   ├── components/                  atomic, unstyled-but-functional
│   │   ├── button.tsx               Button + variants (default/ghost/destructive)
│   │   ├── input.tsx                Input
│   │   ├── textarea.tsx             Textarea (auto-resize variant included)
│   │   ├── label.tsx                Label
│   │   ├── checkbox.tsx             Checkbox
│   │   ├── radio-group.tsx          RadioGroup + RadioGroupItem
│   │   ├── switch.tsx               Switch (toggle)
│   │   ├── select.tsx               Select + SelectItem
│   │   ├── slider.tsx               Slider
│   │   ├── badge.tsx                Badge + variants
│   │   ├── avatar.tsx               Avatar + AvatarFallback
│   │   ├── separator.tsx            Separator (hr)
│   │   ├── skeleton.tsx             Skeleton loader
│   │   └── spinner.tsx              Spinner (indeterminate)
│   │
│   ├── compound/                    composed from primitives — still generic
│   │   ├── dialog.tsx               Dialog + DialogContent + DialogHeader + DialogFooter
│   │   ├── sheet.tsx                Sheet (slide-over panel)
│   │   ├── dropdown-menu.tsx        DropdownMenu + DropdownMenuItem
│   │   ├── context-menu.tsx         ContextMenu + ContextMenuItem
│   │   ├── popover.tsx              Popover + PopoverContent
│   │   ├── tooltip.tsx              Tooltip + TooltipContent
│   │   ├── command.tsx              Command palette (cmdk wrapper)
│   │   ├── tabs.tsx                 Tabs + TabsList + TabsTrigger + TabsContent
│   │   ├── accordion.tsx            Accordion + AccordionItem
│   │   ├── collapsible.tsx          Collapsible + CollapsibleContent
│   │   ├── scroll-area.tsx          ScrollArea (custom scrollbar)
│   │   ├── resizable.tsx            ResizablePanelGroup + ResizablePanel + ResizableHandle
│   │   ├── toast.tsx                Toast + Toaster (sonner wrapper)
│   │   ├── alert.tsx                Alert + AlertTitle + AlertDescription
│   │   └── card.tsx                 Card + CardHeader + CardContent + CardFooter
│   │
│   ├── tokens/                      design tokens (not components)
│   │   ├── colors.ts                color palette constants
│   │   ├── typography.ts            font sizes, weights, line heights
│   │   └── spacing.ts               spacing scale
│   │
│   └── hooks/                       generic UI hooks (no business logic)
│       ├── use-controllable-state.ts
│       ├── use-media-query.ts
│       ├── use-copy-to-clipboard.ts
│       └── use-debounce.ts
│
├── package.json
└── tsconfig.json


════════════════════════════════════════════════════════════
 packages/types/                     @dexpert/types
 Single source of truth for data shapes. Both TS apps and
 Python engine must match these exactly.
════════════════════════════════════════════════════════════

packages/types/
├── src/
│   ├── index.ts
│   ├── agent.ts                     AgentId · AgentStatus · AgentState · AgentConfig
│   ├── task.ts                      TaskPayload · SubTask · PlannerOutput · TaskResult
│   ├── session.ts                   Session · SessionMeta · Checkpoint · ConversationTurn
│   ├── message.ts                   WS protocol:
│   │                                  ClientMessage = TaskMsg | ChatMsg | CancelMsg | PingMsg
│   │                                  EngineEvent = thinking | tool_call | tool_result |
│   │                                                response | agent_status | done | error | pong
│   ├── user.ts                      User · AuthToken · Subscription · UserPreferences
│   ├── tool.ts                      ToolDefinition · ToolCall · ToolResult
│   ├── llm.ts                       ModelConfig · LLMProvider · TokenUsage · CostRecord
│   ├── settings.ts                  EngineSettings · DesktopSettings · AgentModelConfig
│   └── error.ts                     ErrorCode enum · DexpertError · ErrorPayload
│
├── package.json
└── tsconfig.json


════════════════════════════════════════════════════════════
 packages/config/                    @dexpert/config
 Shared build tool configs — no runtime code.
════════════════════════════════════════════════════════════

packages/config/
├── eslint/
│   ├── base.js
│   ├── react.js                     extends base + react-hooks + jsx-a11y
│   └── electron.js                  extends base for main process (no DOM)
├── typescript/
│   ├── base.json
│   ├── react.json                   extends base + jsx settings
│   └── electron-main.json           extends base + CommonJS module
└── tailwind/
    └── base.ts                      shared Tailwind config (fonts, colors, breakpoints)


════════════════════════════════════════════════════════════
 apps/desktop/                       @dexpert/desktop
 Electron 30 + electron-vite + React 18 + TypeScript
 Tailwind CSS + Zustand + react-query

 Auth flow:
   Electron opens → reads keychain (keytar)
   → no valid JWT: opens AuthWindow (800×560, no frame)
     → loads apps/web /auth/login?platform=desktop
     → user logs in via GitHub / Google / email
     → Better Auth issues JWT
     → web redirects to dexpert://token?jwt=...
     → Electron protocol-handler.ts intercepts
     → saves to OS keychain (keytar)
     → AuthWindow closes
   → valid JWT: open MainWindow directly
   MainWindow = agentic chat UI (full app)
════════════════════════════════════════════════════════════

apps/desktop/
│
├── electron/                        Node.js context (main + preload processes)
│   │
│   ├── main/
│   │   ├── index.ts                 App entry point
│   │   │                            - app.whenReady()
│   │   │                            - register protocol handler (dexpert://)
│   │   │                            - start engine subprocess
│   │   │                            - read keychain → open AuthWindow or MainWindow
│   │   │
│   │   ├── app-lifecycle.ts         app.on('before-quit'), app.on('window-all-closed')
│   │   │                            Ensures engine subprocess is killed cleanly
│   │   │
│   │   ├── window/
│   │   │   ├── auth-window.ts       AuthWindow factory
│   │   │   │                        - frameless, 800×560, centered
│   │   │   │                        - loads web/auth/login?platform=desktop
│   │   │   │                        - listens for did-navigate to detect dexpert:// redirect
│   │   │   ├── main-window.ts       MainWindow factory
│   │   │   │                        - frameless, 1280×800, min 900×600
│   │   │   │                        - loads renderer/index.html
│   │   │   │                        - passes ENGINE_WS_URL to renderer via loadURL query
│   │   │   └── window-state.ts      Saves/restores window size + position (electron-store)
│   │   │
│   │   ├── auth/
│   │   │   ├── protocol-handler.ts  app.setAsDefaultProtocolClient('dexpert')
│   │   │   │                        Parses dexpert://token?jwt=... → extracts JWT
│   │   │   │                        Calls token-store.save() → emits 'auth:success'
│   │   │   └── token-store.ts       keytar wrapper
│   │   │                            save(jwt: string): void   → OS keychain
│   │   │                            get(): string | null      ← OS keychain
│   │   │                            clear(): void             on sign-out
│   │   │                            OS keychain = Windows Credential Manager
│   │   │                                         macOS Keychain
│   │   │                                         Linux libsecret
│   │   │
│   │   ├── engine/
│   │   │   ├── engine-manager.ts    Spawn/kill Python engine subprocess
│   │   │   │                        - picks .venv python if present, else system
│   │   │   │                        - waits for "Application startup complete" on stdout
│   │   │   │                        - exponential backoff restart: 1s→2s→4s→8s→16s→give up
│   │   │   │                        - emits: 'ready' | 'stopped' | 'crash'
│   │   │   ├── engine-client.ts     WebSocket client (main process ↔ engine)
│   │   │   │                        - auto-reconnect with backoff
│   │   │   │                        - queues messages while disconnected
│   │   │   │                        - strongly typed: send(msg: ClientMessage)
│   │   │   │                        - on('event', handler: (e: EngineEvent) => void)
│   │   │   ├── engine-health.ts     Polls GET /api/health every 30s
│   │   │   │                        Sends 'engine:degraded' / 'engine:healthy' via IPC
│   │   │   └── engine-port.ts       Finds a free port (default 48765, fallback +1..+10)
│   │   │
│   │   ├── ipc/
│   │   │   ├── channels.ts          Channel name constants — never use raw strings
│   │   │   │                        e.g. IPC.ENGINE_SEND, IPC.ENGINE_EVENTS, IPC.AUTH_*
│   │   │   └── handlers.ts          Registers all ipcMain.handle() calls
│   │   │                            engine:send → engine-client.send()
│   │   │                            engine:events → subscription forwarded to renderer
│   │   │                            auth:get-token → token-store.get()
│   │   │                            auth:clear → token-store.clear()
│   │   │                            shell:open-external → shell.openExternal()
│   │   │                            window:minimize / maximize / close
│   │   │                            app:version → app.getVersion()
│   │   │
│   │   ├── tray.ts                  System tray icon + context menu (show/hide/quit)
│   │   ├── app-menu.ts              Native menu bar (macOS only meaningful)
│   │   └── security.ts              BrowserWindow webPreferences, CSP headers
│   │
│   └── preload/
│       ├── index.ts                 contextBridge.exposeInMainWorld('dexpert', {...})
│       └── index.d.ts               TypeScript declarations for window.dexpert
│                                    window.dexpert.engine.send(msg: ClientMessage): void
│                                    window.dexpert.engine.onEvent(cb): () => void
│                                    window.dexpert.auth.getToken(): Promise<string|null>
│                                    window.dexpert.auth.clearToken(): Promise<void>
│                                    window.dexpert.window.minimize(): void
│                                    window.dexpert.window.maximize(): void
│                                    window.dexpert.window.close(): void
│                                    window.dexpert.shell.openExternal(url): void
│                                    window.dexpert.app.version(): Promise<string>
│
│
├── src/                             Renderer — React, runs in browser sandbox
│   │
│   ├── main.tsx                     createRoot(document.getElementById('root'))
│   │                                Wraps: <QueryClientProvider><App /></QueryClientProvider>
│   ├── index.html
│   │
│   ├── app.tsx                      Root component
│   │                                Reads auth state from auth-store
│   │                                Routes:
│   │                                  loading → <SplashScreen />
│   │                                  unauthenticated → <AuthGate />
│   │                                  authenticated → <AppShell />
│   │
│   ├── components/                  Desktop-specific layout + structural components
│   │                                NOT generic UI primitives (those are in packages/ui)
│   │                                NOT feature components (those are in features/)
│   │   │
│   │   ├── title-bar.tsx            Custom frameless window chrome
│   │   │                            Traffic lights (macOS) / min+max+close (Windows)
│   │   │                            Draggable region (-webkit-app-region: drag)
│   │   │                            Shows app name + engine status dot
│   │   │
│   │   ├── app-shell.tsx            Main authenticated layout
│   │   │                            <TitleBar />
│   │   │                            <ResizablePanelGroup direction="horizontal">
│   │   │                              <ResizablePanel id="sidebar" minSize={15} maxSize={25}>
│   │   │                                <Sidebar />
│   │   │                              </ResizablePanel>
│   │   │                              <ResizableHandle />
│   │   │                              <ResizablePanel id="main">
│   │   │                                <ChatView />            ← center
│   │   │                              </ResizablePanel>
│   │   │                              <ResizableHandle />
│   │   │                              <ResizablePanel id="agents" minSize={20} maxSize={35}>
│   │   │                                <AgentsPanel />
│   │   │                              </ResizablePanel>
│   │   │                            </ResizablePanelGroup>
│   │   │                            <TerminalDrawer />          ← collapsible bottom
│   │   │
│   │   ├── auth-gate.tsx            Shown when unauthenticated
│   │   │                            Displays Dexpert logo + "Opening login..." message
│   │   │                            Calls window.dexpert to open AuthWindow (in main process)
│   │   │                            Listens for auth:success IPC event → updates auth-store
│   │   │
│   │   ├── splash-screen.tsx        Full-screen loading state on first launch
│   │   │                            Shown while engine starts up
│   │   │                            Engine health events → progress indicator
│   │   │
│   │   ├── error-boundary.tsx       React error boundary
│   │   │                            Wraps each major section independently
│   │   │                            Shows inline error panel, not full-screen crash
│   │   │
│   │   ├── engine-status-banner.tsx Shown when engine is degraded/offline
│   │   │                            "Engine reconnecting..." or "Engine offline — retry"
│   │   │
│   │   └── keyboard-shortcuts.tsx   Global hotkey registration (uses use-hotkeys)
│   │                                Cmd+K: command palette
│   │                                Cmd+,: settings
│   │                                Cmd+N: new session
│   │                                Cmd+Shift+T: toggle terminal
│   │
│   │
│   ├── features/                    Feature modules. Each feature is self-contained.
│   │   │                            Rule: a feature may import from packages/ui,
│   │   │                            packages/types, src/stores, src/hooks, src/lib.
│   │   │                            A feature NEVER imports from another feature.
│   │   │
│   │   ├── chat/                    The core conversation interface
│   │   │   ├── index.ts             public exports for this feature
│   │   │   ├── chat-view.tsx        Top-level layout: <MessageList> + <InputBar>
│   │   │   │                        Subscribes to session.store + engine events
│   │   │   ├── message-list.tsx     Virtualised thread (react-virtuoso)
│   │   │   │                        Auto-scrolls to bottom on new messages
│   │   │   ├── message-item.tsx     Polymorphic renderer:
│   │   │   │                          user-message → <UserBubble>
│   │   │   │                          agent-response → <AgentResponse>
│   │   │   │                          tool-call → <ToolCallBlock>
│   │   │   │                          thinking → <ThinkingBlock>
│   │   │   │                          system → <SystemNotice>
│   │   │   ├── user-bubble.tsx      User message — right-aligned, rounded, blue
│   │   │   ├── agent-response.tsx   Agent response — markdown-rendered, with agent badge
│   │   │   ├── tool-call-block.tsx  Collapsible: tool name + input args + result preview
│   │   │   ├── thinking-block.tsx   Collapsible: agent's inner reasoning (italic, muted)
│   │   │   ├── system-notice.tsx    System messages: "Session resumed from checkpoint"
│   │   │   ├── input-bar.tsx        Bottom input area
│   │   │   │                        - multi-line textarea (auto-resize)
│   │   │   │                        - attach file button
│   │   │   │                        - voice record button (→ STT via Groq)
│   │   │   │                        - send button (Enter to send, Shift+Enter newline)
│   │   │   │                        - agent selector pill (which agent to route to)
│   │   │   ├── voice-recorder.tsx   Voice recording UI
│   │   │   │                        - waveform visualiser (Web Audio API)
│   │   │   │                        - sends audio blob to engine via WS
│   │   │   │                        - engine returns transcript → fills textarea
│   │   │   ├── typing-indicator.tsx Three-dot pulse animation while agent streams
│   │   │   ├── chat-header.tsx      Session title (editable inline) + model indicator
│   │   │   └── markdown-renderer.tsx  remark + rehype pipeline
│   │   │                              Code blocks: shiki syntax highlighting
│   │   │                              Inline code, tables, blockquotes, lists
│   │   │
│   │   ├── sidebar/                 Left panel — navigation + session history
│   │   │   ├── index.ts
│   │   │   ├── sidebar.tsx          Layout: logo + new-session + session-list + user-footer
│   │   │   ├── session-list.tsx     Grouped by date (Today / Yesterday / This week / Older)
│   │   │   │                        Each item: title + timestamp + context menu
│   │   │   ├── session-item.tsx     Single session row
│   │   │   │                        - inline rename on double-click
│   │   │   │                        - right-click: rename / export / delete
│   │   │   ├── project-picker.tsx   Workspace/project context selector
│   │   │   │                        Affects which files OS agent can see
│   │   │   ├── search-sessions.tsx  Fuzzy search across session titles + content
│   │   │   └── user-footer.tsx      Avatar + name + plan badge + sign-out button
│   │   │
│   │   ├── agents-panel/            Right panel — live agent activity
│   │   │   ├── index.ts
│   │   │   ├── agents-panel.tsx     Layout: header + agent-cards + token-usage
│   │   │   ├── agent-card.tsx       Per-agent card (Planner / Browser / OS)
│   │   │   │                        - status indicator: idle / running / error
│   │   │   │                        - current action description (streaming text)
│   │   │   │                        - expand → shows last N tool calls
│   │   │   │                        - purple (planner), teal (browser), coral (OS)
│   │   │   ├── tool-call-log.tsx    Full ordered log of all tool calls this session
│   │   │   │                        Shows: agent badge + tool name + duration + result preview
│   │   │   ├── browser-preview.tsx  Live frame from browser agent
│   │   │   │                        JPEG frames received via EngineEvent type 'screenshot'
│   │   │   │                        Lazy: only mounts when browser agent is active
│   │   │   ├── os-activity-log.tsx  UIA events + window scans + install progress
│   │   │   │                        Shows: window title, action taken, outcome
│   │   │   └── token-usage.tsx      Running cost display
│   │   │                            Reads from EngineEvent type 'token_usage'
│   │   │                            Shows: provider icon + tokens + cost in USD
│   │   │
│   │   ├── terminal/                Bottom collapsible terminal drawer
│   │   │   ├── index.ts
│   │   │   ├── terminal-drawer.tsx  Resizable bottom panel (default 200px, drag handle)
│   │   │   │                        Cmd+Shift+T to toggle
│   │   │   ├── terminal-tabs.tsx    Tab bar: + button, close button per tab
│   │   │   └── terminal-instance.tsx  xterm.js terminal
│   │   │                            PTY managed by engine (via IPC → engine spawns pty)
│   │   │
│   │   ├── command-palette/         Cmd+K overlay
│   │   │   ├── index.ts
│   │   │   ├── command-palette.tsx  <Command> (cmdk) in a <Dialog>
│   │   │   │                        Search: sessions / settings pages / actions
│   │   │   ├── session-commands.tsx New session, switch session, export
│   │   │   ├── action-commands.tsx  Quick actions: clear context, switch model, etc.
│   │   │   └── settings-commands.tsx  Navigate to any settings section
│   │   │
│   │   └── settings/                Settings modal — routed by section
│   │       ├── index.ts
│   │       ├── settings-modal.tsx   <Dialog fullscreen> with sidebar navigation
│   │       │                        Left: section list
│   │       │                        Right: section content (lazy-loaded)
│   │       ├── sections/
│   │       │   ├── general.tsx      Appearance (theme: light/dark/system)
│   │       │   │                    Language, date format
│   │       │   │                    Startup behaviour (start minimised, tray on close)
│   │       │   │
│   │       │   ├── models.tsx       Per-agent model selection
│   │       │   │                    Planner model → engine DexpertSettings
│   │       │   │                    Browser model → engine DexpertSettings
│   │       │   │                    OS model → engine DexpertSettings
│   │       │   │                    Global model override toggle
│   │       │   │                    Temperature, max_tokens per agent
│   │       │   │
│   │       │   ├── agents.tsx       Enable/disable each agent
│   │       │   │                    Task timeout (per agent, in seconds)
│   │       │   │                    Max retries, delegation depth
│   │       │   │                    Saved to engine settings (written to defaults.yaml)
│   │       │   │
│   │       │   ├── voice.tsx        STT provider (Groq Whisper)
│   │       │   │                    Mic device selector (enumerates audio inputs)
│   │       │   │                    Silence threshold + duration
│   │       │   │                    Push-to-talk hotkey (default F2)
│   │       │   │
│   │       │   ├── integrations.tsx API key management
│   │       │   │                    Google AI (Gemini) — primary
│   │       │   │                    Groq — STT + fallback
│   │       │   │                    NVIDIA NIM — Kimi k2.5
│   │       │   │                    Anthropic Claude — optional
│   │       │   │                    OpenAI — optional
│   │       │   │                    Keys saved encrypted via engine endpoint
│   │       │   │                    (never stored in renderer, sent once on save)
│   │       │   │
│   │       │   ├── shortcuts.tsx    Keybinding editor
│   │       │   │                    Lists all registered shortcuts
│   │       │   │                    Click to rebind, Escape to cancel
│   │       │   │                    Saved in electron-store (main process)
│   │       │   │
│   │       │   ├── account.tsx      User profile (avatar, name, email — from web API)
│   │       │   │                    Plan/subscription status
│   │       │   │                    Sign out button (clears keychain)
│   │       │   │
│   │       │   └── about.tsx        App version, engine version
│   │       │                        Changelog link, check for updates
│   │       │                        Open-source licenses
│   │       │
│   │       └── settings-nav.tsx     Left sidebar navigation for settings sections
│   │
│   │
│   ├── stores/                      Zustand — client-side state only
│   │   │                            Rule: stores do NOT fetch data. They receive data
│   │   │                            from hooks, and expose actions + selectors.
│   │   │
│   │   ├── auth.store.ts            { user, isAuthenticated, isLoading }
│   │   │                            Actions: setUser, clearUser
│   │   │
│   │   ├── session.store.ts         { activeSessions, currentSessionId, messages }
│   │   │                            Actions: addMessage, updateMessage, setActive
│   │   │                            Persisted to indexedDB (idb-keyval) for offline access
│   │   │
│   │   ├── agents.store.ts          { agentStatuses, toolCallLog, currentTasks }
│   │   │                            Actions: setAgentStatus, addToolCall, setCurrentTask
│   │   │                            Fed by engine WebSocket events
│   │   │
│   │   ├── engine.store.ts          { connectionStatus, engineVersion, lastHealthCheck }
│   │   │                            Actions: setStatus, setVersion
│   │   │
│   │   └── ui.store.ts              { sidebarWidth, agentsPanelWidth, terminalHeight }
│   │                                { terminalOpen, settingsSection, theme }
│   │                                Persisted in electron-store via IPC
│   │
│   │
│   ├── hooks/                       Custom hooks — bridge between stores and features
│   │   │                            Rule: hooks may call window.dexpert (preload API)
│   │   │                            and web API. Features call hooks, not preload directly.
│   │   │
│   │   ├── use-engine.ts            Manages WS event subscription
│   │   │                            useEffect: subscribe to window.dexpert.engine.onEvent
│   │   │                            Dispatches events to correct stores
│   │   │
│   │   ├── use-send-task.ts         Sends task/chat to engine
│   │   │                            Adds optimistic user message to session.store
│   │   │                            Calls window.dexpert.engine.send()
│   │   │
│   │   ├── use-session.ts           CRUD for sessions
│   │   │                            GET /api/sessions → session.store
│   │   │                            POST to create, DELETE to remove
│   │   │
│   │   ├── use-auth.ts              Reads auth.store
│   │   │                            getToken() via window.dexpert.auth
│   │   │                            Exposes signOut() → clears keychain + store
│   │   │
│   │   ├── use-voice.ts             MediaRecorder API
│   │   │                            Sends audio blob to engine for STT
│   │   │                            Returns: { isRecording, startRecording, stopRecording }
│   │   │
│   │   ├── use-settings.ts          Reads/writes settings via engine API
│   │   │                            GET /api/settings → engine DexpertSettings
│   │   │                            PATCH → engine updates defaults.yaml
│   │   │
│   │   └── use-engine-health.ts     Reads engine.store connectionStatus
│   │                                Returns: 'starting' | 'ready' | 'degraded' | 'offline'
│   │
│   │
│   └── lib/                         Pure utility functions — no React, no state
│       ├── api-client.ts            HTTP client to apps/web API routes
│       │                            Injects JWT from window.dexpert.auth.getToken()
│       │                            401 → clears auth, shows sign-in
│       ├── date.ts                  Date formatting utilities
│       ├── markdown.ts              remark + rehype pipeline config
│       ├── cn.ts                    clsx + tailwind-merge (className helper)
│       └── constants.ts             App-wide constants (ENGINE_DEFAULT_PORT etc.)
│
│
├── resources/
│   └── icons/
│       ├── icon.ico                 Windows
│       ├── icon.icns                macOS
│       └── icon.png                 Linux + fallback
│
├── electron.vite.config.ts
├── electron-builder.config.ts
├── package.json
└── tsconfig.json


════════════════════════════════════════════════════════════
 apps/web/                           @dexpert/web
 Next.js 15 App Router + Better Auth + Drizzle ORM
 Deployed separately (Vercel / self-hosted)
 Electron opens its /auth/login page in an AuthWindow
════════════════════════════════════════════════════════════

apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx               Root: fonts, metadata, theme provider
│   │   │
│   │   ├── (auth)/                  Route group — minimal layout, no nav
│   │   │   ├── layout.tsx           Centered card layout, Dexpert logo
│   │   │   ├── login/
│   │   │   │   └── page.tsx         Login page
│   │   │   │                        - GitHub OAuth button
│   │   │   │                        - Google OAuth button
│   │   │   │                        - Email + password form
│   │   │   │                        - "No account? Sign up" link
│   │   │   │                        - Reads ?platform=desktop query param
│   │   │   │                        - On success: if platform=desktop →
│   │   │   │                            redirect dexpert://token?jwt=...
│   │   │   │                          else → redirect to (dashboard)/
│   │   │   ├── signup/
│   │   │   │   └── page.tsx         Sign-up form (email + password)
│   │   │   │                        Triggers verification email
│   │   │   └── verify/
│   │   │       └── page.tsx         Email verification landing
│   │   │                            Shows success state, starts session
│   │   │
│   │   ├── (dashboard)/             Route group — requires auth, has nav
│   │   │   ├── layout.tsx           Nav sidebar + topbar
│   │   │   ├── page.tsx             Dashboard home (usage stats, recent sessions)
│   │   │   └── settings/
│   │   │       └── page.tsx         Web account settings (profile, billing, API keys)
│   │   │
│   │   └── api/
│   │       ├── auth/
│   │       │   └── [...betterauth]/
│   │       │       └── route.ts     Better Auth catch-all
│   │       │                        /api/auth/sign-in/email
│   │       │                        /api/auth/sign-in/social?provider=github
│   │       │                        /api/auth/sign-in/social?provider=google
│   │       │                        /api/auth/verify-email
│   │       │                        /api/auth/sign-out
│   │       │                        /api/auth/get-session
│   │       ├── tokens/
│   │       │   └── route.ts         POST /api/tokens/verify
│   │       │                        Electron calls this on startup to validate stored JWT
│   │       │                        Returns: { valid: boolean, user: User | null }
│   │       ├── users/
│   │       │   └── route.ts         GET|PATCH /api/users/me (requires auth header)
│   │       └── sessions/
│   │           └── route.ts         GET /api/sessions (proxies to engine, requires auth)
│   │
│   ├── lib/
│   │   ├── auth.ts                  Better Auth server config
│   │   │                            providers: GitHub, Google, email+password
│   │   │                            session: JWT (30-day expiry, refreshed on use)
│   │   │                            secret: process.env.BETTER_AUTH_SECRET
│   │   ├── auth-client.ts           Better Auth React client
│   │   ├── db.ts                    Drizzle client (SQLite dev / PostgreSQL prod)
│   │   └── db-schema.ts             users, accounts, sessions tables
│   │
│   └── components/
│       ├── auth-form.tsx            Shared email + password form (login + signup)
│       ├── oauth-buttons.tsx        GitHub + Google sign-in buttons
│       └── desktop-redirect.tsx     Detects platform=desktop, triggers dexpert:// redirect
│
├── drizzle.config.ts
├── next.config.ts
├── package.json
└── tsconfig.json


════════════════════════════════════════════════════════════
 apps/cli/                           @dexpert/cli
════════════════════════════════════════════════════════════

apps/cli/
├── src/
│   ├── index.ts                     Commander entry
│   │                                dexpert run "goal" [--agent planner|browser|os]
│   │                                dexpert interactive
│   │                                dexpert status
│   ├── commands/
│   │   ├── run.ts                   Single task execution
│   │   ├── interactive.ts           Interactive REPL session
│   │   └── status.ts               Show engine health + agent statuses
│   └── tui/                         Ink (React for terminal) components
│       ├── app.tsx                  Ink root
│       ├── chat-view.tsx            Scrollable message list in terminal
│       ├── agent-status-bar.tsx     Single-line: Planner ● Browser ○ OS ○
│       ├── input-line.tsx           Prompt input (ink-text-input)
│       └── thinking-spinner.tsx     Spinner while agent streams
├── package.json
└── tsconfig.json


════════════════════════════════════════════════════════════
 engine/                             Python MAS — PCAgent rearchitected
 Runs as subprocess (Electron) or standalone (CLI / dev)
════════════════════════════════════════════════════════════

engine/
├── main.py                          FastAPI + uvicorn entry
│                                    Prints "Application startup complete" on ready
│                                    (Electron engine-manager.ts watches for this)
├── main_tui.py                      Original PCAgent TUI — kept for reference
├── pyproject.toml                   [tool.ruff], [tool.pytest], [project.scripts]
├── requirements.txt
├── .env                             (gitignored)
├── .env.example
│
├── api/
│   ├── __init__.py
│   ├── server.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── sessions.py
│   │   ├── agents.py
│   │   ├── settings.py
│   │   └── extensions.py            NEW
│   │       GET  /api/extensions/mcp                list all configured MCP servers
│   │       POST /api/extensions/mcp                add a new MCP server config
│   │       DELETE /api/extensions/mcp/{id}         remove a server
│   │       POST /api/extensions/mcp/{id}/connect   force-connect a server
│   │       POST /api/extensions/mcp/{id}/disconnect
│   │       GET  /api/extensions/mcp/discover       run discoverer, return found servers
│   │       POST /api/extensions/mcp/install        install + connect a new MCP package
│   │       GET  /api/extensions/plugins            list installed plugins
│   │       POST /api/extensions/plugins/install    install plugin from marketplace
│   │       POST /api/extensions/plugins/upload     upload local .py file
│   │       DELETE /api/extensions/plugins/{id}     uninstall
│   │       POST /api/extensions/plugins/{id}/toggle enable or disable
│   │       GET  /api/extensions/tools              all tools from all sources (unified view)
│   │
│   └── websocket/
│       ├── __init__.py
│       ├── handler.py
│       ├── manager.py
│       └── protocol.py
│           Extension events emitted to renderer:
│             extension:mcp:connected    { serverId, serverName, tools[] }
│             extension:mcp:disconnected { serverId, reason }
│             extension:mcp:error        { serverId, error }
│             extension:mcp:tools_updated{ serverId, tools[] }
│             extension:plugin:loaded    { pluginId, pluginName, tools[] }
│             extension:plugin:error     { pluginId, error }
│             extension:discovery:result { discovered: McpServerConfig[] }
│             extension:install:proposal { taskId, toolName, suggestedServer }
│             extension:install:progress { packageId, step, percent }
│             extension:install:done     { packageId, serverId }
│             extension:install:failed   { packageId, error }
│
│
├── extensions/                        THE MODERN AI PLATFORM LAYER
│   ├── __init__.py
│   ├── manager.py                     ExtensionManager
│   │   Responsibilities:
│   │   - Called by main.py during startup (after FastAPI is ready)
│   │   - Reads config/mcp_servers.json → connects each enabled MCP server
│   │   - Scans extensions/plugins/userland/ → loads each .py plugin
│   │   - Registers all tools into tools/registry.py (UnifiedToolRegistry)
│   │   - Watchdog: monitors each MCP server process, restarts on crash
│   │   - Hot-reload: watchdog on userland/ dir → reloads changed plugins
│   │   - Emits extension:* events via websocket/manager.py
│   │   - Exposes: get_all_tools(), get_mcp_clients(), get_plugins()
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   │
│   │   ├── client.py                  McpClient — core MCP implementation
│   │   │   Responsibilities:
│   │   │   - Connects to one MCP server (stdio or SSE transport)
│   │   │   - JSON-RPC 2.0 message framing
│   │   │   - Performs MCP handshake: initialize → initialized
│   │   │   - Capability negotiation: lists what server supports
│   │   │   - Async: tools/list → returns list of McpTool
│   │   │   - Async: tools/call(name, arguments) → returns ToolResult
│   │   │   - Async: resources/list → returns list of McpResource
│   │   │   - Async: resources/read(uri) → returns resource content
│   │   │   - Async: prompts/list → returns list of McpPrompt
│   │   │   - Async: prompts/get(name, arguments) → returns rendered prompt
│   │   │   - Handles server-sent notifications (tools/list_changed, etc.)
│   │   │   - Reconnection logic with exponential backoff
│   │   │
│   │   ├── server_process.py          McpServerProcess
│   │   │   Responsibilities:
│   │   │   - Spawns external MCP server binary as subprocess
│   │   │   - Supports: Node.js (npx), Python (uvx/pip), Go binaries, anything in PATH
│   │   │   - Manages stdin/stdout pipes for stdio transport
│   │   │   - Monitors process health, emits 'crash' event to ExtensionManager
│   │   │   - Captures stderr → structured log entries
│   │   │   - Graceful shutdown: sends SIGTERM, waits, then SIGKILL
│   │   │
│   │   ├── protocol.py                MCP spec Pydantic models
│   │   │   JsonRpcRequest / JsonRpcResponse / JsonRpcNotification
│   │   │   InitializeParams / InitializeResult
│   │   │   ServerCapabilities / ClientCapabilities
│   │   │   Tool / ToolInputSchema / CallToolRequest / CallToolResult
│   │   │   Resource / ReadResourceRequest / ReadResourceResult
│   │   │   Prompt / GetPromptRequest / GetPromptResult
│   │   │   ListChangedNotification
│   │   │
│   │   ├── discoverer.py              McpDiscoverer — SELF-ADAPT mechanism #2
│   │   │   Responsibilities:
│   │   │   - Scans these locations for known MCP server packages:
│   │   │       $PATH for executables matching mcp-* pattern
│   │   │       npm global: npm list -g --json → filter @modelcontextprotocol/*
│   │   │       pip global: pip list --format=json → filter mcp-* packages
│   │   │       uvx: uv tool list
│   │   │       ~/.dexpert/mcp-servers/ (user-installed binaries)
│   │   │       /usr/local/bin/mcp-* (system-installed)
│   │   │   - Returns: list[McpServerConfig] (auto-populated command + args)
│   │   │   - Called on startup AND via GET /api/extensions/mcp/discover
│   │   │   - Compares against mcp_servers.json → emits only NEW discoveries
│   │   │
│   │   └── installer.py               McpInstaller — SELF-ADAPT mechanism #3
│   │       Responsibilities:
│   │       - Given a package spec (e.g. "@modelcontextprotocol/server-filesystem")
│   │         installs it via the correct package manager:
│   │           npx -y <spec>   for npm packages
│   │           uvx <spec>      for Python packages
│   │           cargo install   for Rust crates
│   │       - After install: detects binary path, generates McpServerConfig
│   │       - Appends to mcp_servers.json
│   │       - Calls ExtensionManager.connect_server() immediately
│   │       - Emits install:progress events throughout
│   │       - Used by: POST /api/extensions/mcp/install
│   │         AND by: Planner agent when it detects a missing capability
│   │
│   │
│   └── plugins/
│       ├── __init__.py
│       │
│       ├── base_plugin.py             BasePlugin — abstract class
│       │   Every plugin must implement:
│       │     MANIFEST: PluginManifest  (class-level, validated on load)
│       │     async setup(settings: DexpertSettings) → None
│       │     async teardown() → None
│       │     get_tools() → list[ToolDefinition]
│       │   Optional:
│       │     async on_task_start(task: TaskPayload) → None
│       │     async on_task_done(result: TaskResult) → None
│       │     async on_session_start(session_id: str) → None
│       │
│       ├── loader.py                  PluginLoader
│       │   - Uses importlib.util.spec_from_file_location() to load .py files
│       │   - Validates that class inherits BasePlugin
│       │   - Validates MANIFEST against PluginManifest schema
│       │   - Runs in executor (thread) to isolate blocking setup()
│       │   - Catches all exceptions — one broken plugin never crashes the engine
│       │   - Returns: loaded plugin instance or LoadError
│       │
│       ├── sandbox.py                 PluginSandbox
│       │   - Restricts what plugins can import via sys.meta_path hook
│       │   - Allowed: standard lib, requests, httpx, playwright, pillow, numpy
│       │   - Blocked: os.system, subprocess, socket (unless plugin declares permission)
│       │   - Plugin permissions declared in MANIFEST.permissions[]
│       │   - Permission list: network · filesystem · subprocess · system · clipboard
│       │   - Permissions shown to user in Plugin UI before install
│       │
│       ├── validator.py               PluginValidator
│       │   - Validates MANIFEST completeness and schema correctness
│       │   - Checks tool definitions are valid ToolDefinition instances
│       │   - Verifies declared permissions are from the allowed set
│       │   - Static analysis: scans for banned API calls vs declared permissions
│       │
│       ├── registry.py                PluginRegistry
│       │   - Maintains { plugin_id → BasePlugin instance }
│       │   - Tracks enabled/disabled state (persisted to config/plugins.json)
│       │   - Iterates enabled plugins to collect tools for UnifiedToolRegistry
│       │
│       ├── userland/                  User-installed plugin .py files live here
│       │   ├── .gitkeep
│       │   └── (user installs go here — gitignored except .gitkeep)
│       │
│       └── marketplace/               Curated plugin index
│           ├── index.json             List of available plugins with metadata
│           │                          { id, name, version, description, author,
│           │                            download_url, sha256, permissions[], tools[] }
│           └── .gitkeep
│
├── agents/
│   ├── __init__.py
│   ├── base.py                      BaseAgent: abstract run(), stream_callback, settings
│   ├── planner/
│   │   ├── __init__.py
│   │   ├── agent.py                 Central router
│   │   │                            - calls planner.plan() to decompose goal
│   │   │                            - dispatches subtasks in dependency order
│   │   │                            - saves checkpoint after each subtask
│   │   │                            - handles subtask failure gracefully
│   │   │                            - emits agent_status events throughout
│   │   │                            PlannerAgent.chat() → conversational response
│   │   ├── models.py                Plan, SubTask, PlannerConfig (Pydantic)
│   │   └── config/
│   │       ├── prompts.yaml
│   │       └── settings.yaml
│   ├── browser/
│   │   ├── __init__.py
│   │   ├── agent.py                 BrowserAgent.run(task, session_id)
│   │   ├── memory.py                Browser-session-scoped memory
│   │   ├── context.py               Browser task context
│   │   ├── manager.py               Playwright browser lifecycle
│   │   ├── state.py                 Browser agent state machine
│   │   ├── config/
│   │   │   ├── prompt.yaml
│   │   │   └── settings.yaml
│   │   ├── controller/
│   │   │   ├── __init__.py
│   │   │   ├── interaction.py       click, type, scroll, hover, select
│   │   │   └── navigation.py        navigate, wait_for, back, forward
│   │   ├── perception/
│   │   │   ├── __init__.py
│   │   │   ├── perception.py        Screenshot → LLM vision pipeline
│   │   │   ├── service.py           Async perception service
│   │   │   ├── processor.js         DOM processing (Node.js script, called via subprocess)
│   │   │   └── captcha/
│   │   │       ├── __init__.py
│   │   │       └── solver.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       └── registry.py
│   └── os/
│       ├── __init__.py
│       ├── agent.py                 OSAgent.run(task, session_id)
│       ├── context.py
│       ├── state.py
│       ├── config/
│       │   ├── prompt.yaml
│       │   └── settings.yaml
│       ├── controller/
│       │   ├── __init__.py
│       │   ├── execution.py         Shell commands, script execution
│       │   ├── filesystem.py        File CRUD, directory ops
│       │   ├── interaction.py       Mouse + keyboard synthetic events (pyautogui)
│       │   ├── network.py           Network checks
│       │   └── system.py            Processes, system info, install (winget/brew/apt)
|       |
│       ├── middleware/    # **THE SECRET SAUCE (Silent Interceptors)**
│       │   ├── vfs_router.py  # Dynamic CWD: Translates paths, auto-injects .venv paths
│       │   ├── ast_mapper.py  # Background Tree-Sitter repo scanner (Holographic Context)
│       │   └── pty_manager.py # Persistent Terminal Spawning & Log Scraping
│       │
│       ├── perception/
│       │   ├── __init__.py
│       │   ├── bridge.py            Python → Rust binary (subprocess, JSON stdio)
│       │   ├── perception.py        High-level perception API
│       │   ├── processor.py         UIA result processing
│       │   └── native/              Standalone Rust binary (NOT napi-rs)
│       │       ├── Cargo.toml       Compiles to: dexpert-perception.exe
│       │       ├── Cargo.lock
│       │       └── src/
│       │           ├── main.rs      CLI: reads JSON from stdin, writes to stdout
│       │           ├── models.rs    WindowNode, UIElement structs (serde JSON)
│       │           └── platforms/
│       │               ├── mod.rs
│       │               ├── windows.rs   UIAutomation COM (windows-rs crate)
│       │               ├── macos.rs     NSAccessibility / AXUIElement
│       │               └── linux.rs     AT-SPI2 D-Bus (dbus-rs)
│       ├── test/
│       │   ├── last_ui_tree.txt
│       │   ├── test_interaction.py
│       │   ├── test_table_logic.py
│       │   └── test_uia.py
│       └── tools/
│           ├── __init__.py
│           ├── models.py
│           └── registry.py
│
├── core/
│   ├── __init__.py
│   ├── session/                     # ➔ Replaces monolithic session.py
│   │   ├── __init__.py
│   │   ├── manager.py               # Lifecycle (create, resume, pause, archive)
│   │   ├── checkpoint.py            # Serializes active tasks to disk for crash recovery
│   │   └── history.py               # Manages message appends and retrieval
│   │
│   ├── protocol/                    # ➔ Replaces monolithic protocol.py
│   │   ├── __init__.py
│   │   ├── messages.py              # Pydantic schemas (TaskMsg, ChatMsg, ErrorMsg)
│   │   └── events.py                # WebSocket events (AgentStatus, StreamingToken)
│   │
│   ├── scratchpad.py                Temporary per-task reasoning store
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              DexpertSettings (Pydantic)
│   │   │                            All settings readable via GET /api/settings
│   │   │                            All settings writable via PATCH /api/settings
│   │   └── defaults.yaml            Default values loaded at startup
│   │
│   ├── llm/                         # ➔ Consolidated Intelligence Layer
│   │   ├── __init__.py
│   │   ├── client.py                # 1-for-All LiteLLM router (Gemini, Groq, etc.)
│   │   ├── cache.py                 # Native Prompt Caching Manager
│   │   ├── parser.py                # Extracts <thinking>, <action>, <done> reliably
│   │   └── tokenizer.py             # Moved here! Cost & token tracking logic
│   │                      
│   ├── context/           # **LEVEL 4.5 CONTEXT ENGINEERING**
│   │   ├── episodic.py    # Wipes ReAct Action History after every item completion
│   │   ├── hud.py         # Injects the "North Star" read-only panel at the top of prompts
│   │   └── strategy.py    # Extracts procedural "rules" before wiping history
│   │
│   └── memory/            # Persistence & State
│       ├── state_ledger.py # The Omni-Queue! Tracks 1-100% confidence scores & completion status
│       ├── database.py     # SQLite operations
│       └── personalization.py # Background extractor for user preferences
│
├── tools/
│   ├── registry.py                    UnifiedToolRegistry
│   │   Responsibilities:
│   │   - Single source of truth for all available tools
│   │   - Namespaced by source:
│   │       native:run_command         built-in catalog tools
│   │       plugin:github:create_pr    from plugins
│   │       mcp:filesystem:read_file   from MCP servers
│   │   - register_native(tools: list[ToolDefinition])
│   │   - register_plugin(plugin_id, tools: list[ToolDefinition])
│   │   - register_mcp(server_id, tools: list[McpTool])
│   │   - unregister_plugin(plugin_id)    on plugin disable/unload
│   │   - unregister_mcp(server_id)       on MCP server disconnect
│   │   - get_all() → list[UnifiedTool]   full list for agent system prompts
│   │   - get_for_agent(role) → list      filtered by agent capabilities
│   │   - find(name: str) → UnifiedTool   lookup by namespaced name
│   │   - dispatch(call: ToolCall) → ToolResult
│   │       routes to: native catalog / plugin.execute() / mcp_client.call_tool()
│   │   - Emits: tools_changed event via websocket when tool list changes
│   │   - Thread-safe: asyncio.Lock protects all mutations
│   ├── models.py                    ToolDefinition, ToolCall, ToolResult base models
│   └── clipboard_tools.py           Clipboard read/write
│
├── shared/
│   ├── __init__.py
│   ├── security.py                  Input sanitisation, path traversal checks
│   └── serialisation.py             JSON helpers, Pydantic → dict utilities
│
├── utils/                           # Pure, Domain-Agnostic Helpers
│   ├── __init__.py
│   ├── logger.py                    # Structured JSON logging {ts, level, module, event}
│   ├── exceptions.py                # Global DexpertError, ErrorCodes (Typo fixed)
│   ├── security.py                  # Path traversal blocks, input sanitization
│   └── serialization.py             # Safe JSON parsing, Pydantic → dict helpers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  Shared: mock settings, mock LLM, test db
│   ├── test_browser.py
│   ├── test_memory_pipeline.py
│   ├── test_planner.py
│   ├── test_tokens.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │
│   └── fixtures/
│       ├── sample_session.json
│       └── memory.db
│
└── runtime/                         Gitignored. All generated at runtime.
    ├── sessions/
    ├── workspace/
    ├── downloads/
    ├── logs/
    │   ├── dexpert.log
    │   └── token_tracker.jsonl
    ├── tmp/
    └── memory.db


════════════════════════════════════════════════════════════
 BOUNDARY RULES (what makes this never fail)
════════════════════════════════════════════════════════════

packages/ui/ rules:
  ✓ React + Tailwind only
  ✓ No window.dexpert calls
  ✓ No API calls
  ✓ No Zustand
  ✗ Never import from apps/*

apps/desktop/src/features/* rules:
  ✓ May import from packages/ui
  ✓ May import from packages/types
  ✓ May import from src/stores/*
  ✓ May import from src/hooks/*
  ✓ May import from src/lib/*
  ✗ Never import from another feature
  ✗ Never call window.dexpert directly (use hooks/)

apps/desktop/src/hooks/* rules:
  ✓ Only place that calls window.dexpert (preload bridge)
  ✓ Only place that calls api-client.ts
  ✓ Dispatches received data into stores

apps/desktop/src/stores/* rules:
  ✓ State only — no side effects
  ✓ No API calls, no window.dexpert
  ✓ Actions accept data and update state

electron/main/* rules:
  ✓ Node.js only — no React, no browser APIs
  ✓ All engine communication through engine-client.ts
  ✓ All auth through token-store.ts
  ✓ All renderer communication through ipc/handlers.ts

engine/ rules:
  ✓ All external-facing messages validated by Pydantic
  ✓ All failures → typed DexpertError with error_code
  ✓ error_code values match packages/types/error.ts ErrorCode enum exactly
  ✓ LLM calls always go through core/llm/client.py (circuit breaker included)
  ✓ All DB writes in transactions
  ✓ Checkpoint saved after every completed subtask