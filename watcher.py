import os
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Constants & Globals ---
UNCHECKED = '☐ '
CHECKED = '☑ '

class CodeWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Real-Time Context Watcher")
        self.root.geometry("1150x750")

        # Configurations
        self.root_path = tk.StringVar(value=os.getcwd())
        self.output_file = tk.StringVar(value="LLM_Context.txt")
        self.included_exts = tk.StringVar(value=".py, .yaml, .yml, .env, .js, .ts, .tsx, .css, .json, .env.local, .prisma, .rs, .toml, .md, .html")
        self.hard_excludes = tk.StringVar(value="node_modules, .git, .venv, __pycache__, dist, build, target, .next, AgentUI, ui, .pcagent_browser_profile, .pcagent_temp, .idea, .vscode")
        
        # State variables
        self.item_mapping = {}  
        self.debounce_timer = None
        self.observer = None
        self.is_generating = False

        self.setup_ui()
        self.setup_watcher()
        self.refresh_tree()

    def setup_ui(self):
        # Top Frame: Path Selection
        top_frame = tk.Frame(self.root, padx=10, pady=5)
        top_frame.pack(fill="x")
        
        tk.Label(top_frame, text="Root Path:").pack(side="left")
        tk.Entry(top_frame, textvariable=self.root_path, width=60).pack(side="left", padx=5)
        tk.Button(top_frame, text="Browse", command=self.browse_root).pack(side="left", padx=5)
        tk.Button(top_frame, text="Refresh Tree UI", command=self.refresh_tree, bg="#e0e0e0").pack(side="right", padx=5)

        # Main Body: PanedWindow (Left: Tree, Right: Settings)
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Panel: Treeview UI
        tree_frame = tk.Frame(self.paned)
        self.paned.add(tree_frame, weight=3)

        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(tree_frame, selectmode="none", yscrollcommand=tree_scroll.set)
        self.tree.heading("#0", text="Select Files for Context (Whole Tree is ALWAYS included in output)", anchor='w')
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Bind clicks for checking/unchecking
        self.tree.bind('<Button-1>', self.toggle_item)

        # Right Panel: Settings
        settings_frame = tk.Frame(self.paned, padx=10)
        self.paned.add(settings_frame, weight=1)

        tk.Label(settings_frame, text="Output File Name:").pack(anchor="w", pady=(0, 2))
        tk.Entry(settings_frame, textvariable=self.output_file).pack(fill="x", pady=(0, 10))

        tk.Label(settings_frame, text="Included Extensions (comma separated):").pack(anchor="w")
        tk.Entry(settings_frame, textvariable=self.included_exts).pack(fill="x", pady=(0, 10))

        tk.Label(settings_frame, text="Hard Exclude Folders (comma separated):").pack(anchor="w")
        tk.Entry(settings_frame, textvariable=self.hard_excludes).pack(fill="x", pady=(0, 10))

        tk.Label(settings_frame, text="Regex Exclude Patterns (one per line):").pack(anchor="w")
        self.regex_text = tk.Text(settings_frame, height=8, width=30)
        self.regex_text.pack(fill="x", pady=(0, 10))
        default_regex = "\\.venv[\\\\/]\n__pycache__\n\\.pyc$\n\\.log$\n\\.tmp$\npackage-lock\\.json\npnpm-lock\\.yaml"
        self.regex_text.insert("1.0", default_regex)

        # Bottom Frame: Action Buttons & Auto-Update status
        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill="x")

        self.auto_update_var = tk.BooleanVar(value=True)
        tk.Checkbutton(bottom_frame, text="Auto-update on save (10s delay)", variable=self.auto_update_var).pack(side="left")

        self.auto_mode_var = tk.StringVar(value="Selected Files Only")
        auto_mode_menu = ttk.Combobox(bottom_frame, textvariable=self.auto_mode_var, values=["Selected Files Only", "All Present Eligible Files"], state="readonly", width=25)
        auto_mode_menu.pack(side="left", padx=10)

        # Progress Bar & Status (For Interactivity)
        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate', length=150)
        self.progress.pack(side="left", padx=15)
        
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bottom_frame, textvariable=self.status_var, fg="#333333", font=('Helvetica', 9, 'italic')).pack(side="left", padx=5)

        tk.Button(bottom_frame, text="Generate Context File", command=self.manual_generate, bg="#4CAF50", fg="white", font=('Helvetica', 10, 'bold'), width=20).pack(side="right")

        self.root.bind("<<FileChanged>>", self.handle_file_changed)

    # --- UI Interactions ---
    def browse_root(self):
        folder = filedialog.askdirectory(initialdir=self.root_path.get())
        if folder:
            self.root_path.set(folder)
            self.setup_watcher()
            self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.item_mapping.clear()
        
        base_path = self.root_path.get()
        if not os.path.exists(base_path): return

        root_node = self.tree.insert("", "end", text=UNCHECKED + os.path.basename(base_path) + " (ROOT)", open=True)
        self.item_mapping[root_node] = {'path': base_path, 'type': 'dir'}
        
        self._populate_tree_recursive(base_path, root_node)
        self.status_var.set("Tree Refreshed.")

    def _populate_tree_recursive(self, path, parent_node):
        try:
            items = os.listdir(path)
        except PermissionError: return

        hard_excludes =[e.strip() for e in self.hard_excludes.get().split(',')]
        exts =[e.strip() for e in self.included_exts.get().split(',')]

        dirs, files = [],[]
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                if item not in hard_excludes: dirs.append(item)
            else:
                if os.path.splitext(item)[1] in exts: files.append(item)

        dirs.sort(); files.sort()

        for d in dirs:
            full_path = os.path.join(path, d)
            node = self.tree.insert(parent_node, "end", text=UNCHECKED + d, open=False)
            self.item_mapping[node] = {'path': full_path, 'type': 'dir'}
            self._populate_tree_recursive(full_path, node)

        for f in files:
            full_path = os.path.join(path, f)
            node = self.tree.insert(parent_node, "end", text=UNCHECKED + f)
            self.item_mapping[node] = {'path': full_path, 'type': 'file'}

    def toggle_item(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return

        current_text = self.tree.item(item, "text")
        is_checked = current_text.startswith(CHECKED)
        self.set_item_state(item, not is_checked)

    def set_item_state(self, item, state):
        current_text = self.tree.item(item, "text")
        name = current_text[2:] 
        prefix = CHECKED if state else UNCHECKED
        self.tree.item(item, text=prefix + name)

        for child in self.tree.get_children(item):
            self.set_item_state(child, state)

    # --- Directory Tree String Builder ---
    def generate_ascii_tree(self, dir_path, exts, hard_excludes, regex_patterns, prefix=""):
        tree_lines =[]
        try:
            items = os.listdir(dir_path)
        except PermissionError:
            return []

        valid_items =[]
        for item in items:
            full_path = os.path.join(dir_path, item)
            
            # Skip output file itself
            out_file = os.path.abspath(os.path.join(self.root_path.get(), self.output_file.get()))
            if os.path.abspath(full_path) == out_file:
                continue
                
            if any(p.search(full_path) for p in regex_patterns):
                continue

            if os.path.isdir(full_path):
                if item not in hard_excludes:
                    valid_items.append((item, True))
            else:
                if os.path.splitext(item)[1] in exts:
                    valid_items.append((item, False))

        # Sort: directories first, then files
        valid_items.sort(key=lambda x: (not x[1], x[0].lower()))

        for i, (item, is_dir) in enumerate(valid_items):
            is_last = (i == len(valid_items) - 1)
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{item}")

            if is_dir:
                extension = "    " if is_last else "│   "
                tree_lines.extend(self.generate_ascii_tree(os.path.join(dir_path, item), exts, hard_excludes, regex_patterns, prefix + extension))

        return tree_lines

    # --- Core Generation Logic (Runs in Background Thread) ---
    def get_selected_files(self):
        selected_files =[]
        def walk(item):
            data = self.item_mapping[item]
            if data['type'] == 'file' and self.tree.item(item, "text").startswith(CHECKED):
                selected_files.append(data['path'])
            for child in self.tree.get_children(item):
                walk(child)
        
        for child in self.tree.get_children():
            walk(child)
        return selected_files

    def get_all_eligible_files(self, exts, hard_excludes, regex_patterns):
        eligible =[]
        out_file = os.path.abspath(os.path.join(self.root_path.get(), self.output_file.get()))
        
        for root, dirs, files in os.walk(self.root_path.get()):
            dirs[:] =[d for d in dirs if d not in hard_excludes]
            for f in files:
                if os.path.splitext(f)[1] not in exts: continue
                fpath = os.path.join(root, f)
                
                if os.path.abspath(fpath) == out_file: continue
                if any(p.search(fpath) for p in regex_patterns): continue
                
                eligible.append(fpath)
        return eligible

    def manual_generate(self):
        if self.is_generating: return
        self.start_generation(use_all_files=False)

    def start_generation(self, use_all_files):
        self.is_generating = True
        self.progress.start(10)
        self.status_var.set("Processing files & generating context... Please wait.")
        
        # Run in background to keep GUI responsive
        threading.Thread(target=self._generate_task, args=(use_all_files,), daemon=True).start()

    def _generate_task(self, use_all_files):
        try:
            root_dir = self.root_path.get()
            out_file = os.path.join(root_dir, self.output_file.get())

            exts = [e.strip() for e in self.included_exts.get().split(',')]
            hard_excludes = [e.strip() for e in self.hard_excludes.get().split(',')]
            regex_patterns =[re.compile(e.strip()) for e in self.regex_text.get("1.0", tk.END).split('\n') if e.strip()]

            # 1. Always generate the full structure map
            tree_lines = self.generate_ascii_tree(root_dir, exts, hard_excludes, regex_patterns)
            tree_text = "\n".join(tree_lines)

            # 2. Get the files to actually read
            files_to_process = self.get_all_eligible_files(exts, hard_excludes, regex_patterns) if use_all_files else self.get_selected_files()

            # 3. Write LLM-Optimized Output
            with open(out_file, 'w', encoding='utf-8') as f:
                # LLM Context Prompt Header
                f.write("=" * 80 + "\n")
                f.write("CODEBASE CONTEXT FILE\n")
                f.write("=" * 80 + "\n")
                f.write("SYSTEM PROMPT / INSTRUCTIONS:\n")
                f.write("You are an expert software developer and AI assistant. The following document \n")
                f.write("contains the directory structure and file contents of a specific codebase.\n")
                f.write("Use this context to understand the architecture, logic, and dependencies \n")
                f.write("of the project to accurately answer questions, debug, or write new code.\n")
                f.write("=" * 80 + "\n\n")

                # Directory Structure Map
                f.write("### 1. DIRECTORY STRUCTURE MAP ###\n")
                f.write(f"Root: {os.path.basename(root_dir)}/\n")
                f.write(tree_text if tree_text else "[Empty or No Eligible Files Found]")
                f.write("\n\n" + "=" * 80 + "\n\n")

                # Files Context
                f.write("### 2. FILE CONTENTS ###\n")
                f.write(f"Total Selected Files Included Below: {len(files_to_process)}\n\n")

                for fpath in files_to_process:
                    rel_path = os.path.relpath(fpath, root_dir).replace('\\', '/')
                    
                    # File Start Delimiter
                    f.write(f"--- [FILE START] : {rel_path} ---\n")
                    try:
                        with open(fpath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            f.write(content if content.strip() else "// [File is empty]\n")
                    except Exception as e:
                        f.write(f"// [Error reading file: {str(e)}]\n")
                    
                    # File End Delimiter
                    f.write(f"\n--- [FILE END] : {rel_path} ---\n")
                    
                    # 3 Line Gap for LLM Separation
                    f.write("\n\n\n")
                    
            # Complete! Back to main thread for UI Update
            self.root.after(0, self._finish_generation, True, f"Success! ({len(files_to_process)} files added)")

        except Exception as e:
            self.root.after(0, self._finish_generation, False, str(e))

    def _finish_generation(self, success, msg):
        self.progress.stop()
        self.is_generating = False
        if success:
            self.status_var.set(f"[{time.strftime('%H:%M:%S')}] {msg}")
        else:
            self.status_var.set("Error during generation!")
            messagebox.showerror("Generation Error", f"Failed to save output:\n{msg}")

    # --- Watchdog (Real-time events) ---
    def setup_watcher(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        path = self.root_path.get()
        if not os.path.exists(path): return

        event_handler = UpdateEventHandler(self.root)
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()

    def handle_file_changed(self, event=None):
        if not self.auto_update_var.get() or self.is_generating: return

        if self.debounce_timer:
            self.root.after_cancel(self.debounce_timer)

        self.status_var.set(f"[{time.strftime('%H:%M:%S')}] File change detected. Auto-updating in 10s...")
        self.debounce_timer = self.root.after(10000, self.auto_generate)

    def auto_generate(self):
        use_all = (self.auto_mode_var.get() == "All Present Eligible Files")
        self.start_generation(use_all_files=use_all)


class UpdateEventHandler(FileSystemEventHandler):
    def __init__(self, root_window):
        self.root_window = root_window

    def on_any_event(self, event):
        if event.is_directory: return
        self.root_window.event_generate("<<FileChanged>>")


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = CodeWatcherApp(root)
    root.mainloop()
    
    if app.observer:
        app.observer.stop()
        app.observer.join()