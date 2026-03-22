import os
import shutil
import glob
import fnmatch
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Union, Optional, Any

class FilesystemController:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir).resolve()

    def _resolve_path(self, path: str) -> Path:
        """Resolves path, allowing absolute paths but keeping them relative to CWD if possible, 
        or just trusting absolute paths if outside. 
        Agent usually gives absolute paths.
        """
        # effective_root = self.root # For now we allow full system access if agent has it
        return Path(path).resolve()

    def read_file(self, 
                  path: str, 
                  range: Optional[Dict[str, int]] = None, 
                  format: str = "auto", 
                  extract: Optional[str] = None, 
                  encoding: str = "utf-8", 
                  max_lines: Optional[int] = None, 
                  truncation_strategy: str = "smart", 
                  search_hint: Optional[str] = None) -> Union[str, bytes]:
        
        target = self._resolve_path(path)
        if not target.exists():
            return f"Error: File {target} not found"
        if not target.is_file():
            return f"Error: {target} is not a file"

        ext = target.suffix.lower()
        is_binary = format == "binary"
        if format == "auto":
            if ext in['.png', '.jpg', '.exe', '.dll', '.bin', '.zip']:
                is_binary = True
            elif ext == '.pdf':
                is_binary = False # Try text extraction by default for PDF

        try:
            # ── PDF Specialized Handling ──
            if ext == '.pdf' and not is_binary:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(target)
                    text = ""
                    for page in reader.pages:
                        text += (page.extract_text() or "") + "\n"
                    
                    if not text.strip():
                        return "Error: Could not extract text from PDF (it might be image-based or encrypted)."
                    
                    lines = text.splitlines(keepends=True)
                except ImportError:
                    return "Error: 'pypdf' library not found. Use 'execute_script' to install it or read as binary."
                except Exception as e:
                    return f"Error reading PDF: {e}"
            
            # ── Binary Handling ──
            elif is_binary:
                with open(target, 'rb') as f:
                    content = f.read()
                    if range:
                        start = range.get("start", 0)
                        end = range.get("end", len(content))
                        content = content[start:end]
                    return f"<Binary Data: {len(content)} bytes>" 
            
            # ── Standard Text Handling ──
            else:
                with open(target, 'r', encoding=encoding, errors='replace') as f:
                    lines = f.readlines()

            total_lines = len(lines)
            
            # 1. Truncation / Search Hint Logic
            start_idx = 0
            end_idx = total_lines

            if range:
                # 1-indexed range to 0-indexed slicing
                start_idx = max(0, range.get("start", 1) - 1)
                end_idx = min(total_lines, range.get("end", total_lines))
            
            elif search_hint:
                # Find best match block
                matches =[]
                for i, line in enumerate(lines):
                    if re.search(search_hint, line, re.IGNORECASE):
                        matches.append(i)
                
                if matches:
                    # Center around first match or middle match? Let's pick first for now
                    center = matches[0]
                    window = max_lines or 100
                    half = window // 2
                    start_idx = max(0, center - half)
                    end_idx = min(total_lines, center + half)
                else:
                    # Fallback if not found
                     if max_lines and total_lines > max_lines:
                         end_idx = max_lines
            
            elif max_lines and total_lines > max_lines:
                if truncation_strategy == "head":
                    end_idx = max_lines
                elif truncation_strategy == "tail":
                    start_idx = total_lines - max_lines
                elif truncation_strategy == "middle":
                    # Middle of file
                    mid = total_lines // 2
                    half = max_lines // 2
                    start_idx = max(0, mid - half)
                    end_idx = min(total_lines, mid + half)
                # 'smart' defaults to head without hint

            relevant_lines = lines[start_idx:end_idx]
            content_str = "".join(relevant_lines)

            # 2. Extract Logic (Simplified for JSON/CSV)
            if extract:
                if format == "json" or target.suffix == ".json":
                    try:
                        data = json.loads(content_str)
                        # primitive json path: "key.initial"
                        keys = extract.split('.')
                        curr = data
                        for k in keys:
                            if isinstance(curr, dict): curr = curr.get(k)
                            elif isinstance(curr, list) and k.isdigit(): curr = curr[int(k)]
                            else: curr = None; break
                        return json.dumps(curr, indent=2)
                    except Exception as e:
                        return f"Extraction Error: {e}"
                # Add more extractors here (CSV, etc)

            footer = ""
            if len(relevant_lines) < total_lines:
                footer = f"\n... (Showing lines {start_idx+1}-{end_idx} of {total_lines})"

            return content_str + footer

        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, path: str, content: str, mode: str = "overwrite", create_parents: bool = True, encoding: str = "utf-8") -> str:
        target = self._resolve_path(path)
        
        if create_parents:
            target.parent.mkdir(parents=True, exist_ok=True)

        file_mode = 'w'
        if mode == "append": file_mode = 'a'
        
        if mode == "insert_at_line":
            return "Error: mode 'insert_at_line' requires 'edit_file' tool."

        try:
            with open(target, file_mode, encoding=encoding) as f:
                f.write(content)
            return f"Success: Wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def edit_file(self, path: str, operations: List[Dict[str, Any]], dry_run: bool = False, allow_multiple_matches: bool = False) -> str:
        """
        SOTA Search/Replace Block Editor & Legacy string editor.
        """
        target = self._resolve_path(path)
        if not target.exists(): return "Error: File not found"

        try:
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for op in operations:
                op_type = op.get("type", "search_replace")
                
                # --- 🚀 NEW SOTA BLOCK REPLACEMENT ---
                if op_type == "search_replace":
                    search_block = op.get("search", "")
                    replace_block = op.get("replace", "")
                    
                    if not search_block:
                        return "Error: 'search' block cannot be empty."

                    # Exact Match Fast Path
                    if search_block in content:
                        count = content.count(search_block)
                        if count > 1 and not allow_multiple_matches:
                            return f"Error: Found {count} exact matches for the search block. Provide a more specific search block or set allow_multiple_matches=True."
                        content = content.replace(search_block, replace_block, 0 if allow_multiple_matches else 1)
                    else:
                        # Fail explicitly on mismatch to prevent code corruption
                        return (
                            f"Error: Search block not found exactly in file.\n"
                            f"Make sure you include the EXACT leading whitespace and existing code.\n"
                            f"Provided search block:\n```\n{search_block}\n```"
                        )
                
                # --- Legacy compatibility support ---
                else:
                    tgt = op.get("target")
                    if isinstance(tgt, int) or (isinstance(tgt, str) and tgt.isdigit()):
                        lines = content.split('\n')
                        idx = int(tgt) - 1
                        if 0 <= idx < len(lines):
                            if op_type == "replace":
                                lines[idx] = op.get("content", "")
                            elif op_type == "delete":
                                lines.pop(idx)
                            elif op_type == "insert":
                                lines.insert(idx, op.get("content", ""))
                        content = '\n'.join(lines)
                    else:
                        tgt_str = str(tgt)
                        if tgt_str in content:
                            if op_type == "replace":
                                content = content.replace(tgt_str, op.get("content", ""), 0 if allow_multiple_matches else 1)
                            elif op_type == "delete":
                                content = content.replace(tgt_str, "", 0 if allow_multiple_matches else 1)

            if dry_run:
                return f"--- DRY RUN ---\n{content}\n--- END DRY RUN ---"
            
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            return "Success: Edit applied."
            
        except Exception as e:
            return f"Error editing file: {e}"

    def list_dir(self, path: str, depth: int = 2, tree: bool = False, ignore: List[str] =[], show_meta: bool = False) -> str:
        target = self._resolve_path(path)
        if not target.exists(): return "Error: Path not found"
        
        output =[]
        default_ignore =[
            ".git", "node_modules", "node_module", "__pycache__", 
            ".next", "dist", "build", "built", "target", "out",
            "venv", ".venv", ".env", "env", "bin", "obj"
        ]
        ignores = set(default_ignore + ignore)

        def walk(p: Path, current_depth: int, prefix: str = ""):
            if depth != -1 and current_depth > depth: return
            
            try:
                entries = sorted(list(p.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
                
                for i, entry in enumerate(entries):
                    if entry.name in ignores: continue
                    
                    is_last = (i == len(entries) - 1)
                    
                    meta = ""
                    if show_meta:
                        stat = entry.stat()
                        size = stat.st_size
                        meta = f" ({size}b)"
                    
                    if tree:
                        connector = "└── " if is_last else "├── "
                        line = f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}{meta}"
                        output.append(line)
                        
                        if entry.is_dir():
                            ext_prefix = "    " if is_last else "│   "
                            walk(entry, current_depth + 1, prefix + ext_prefix)
                    else:
                        rel_path = entry.relative_to(target)
                        output.append(f"{rel_path}{'/' if entry.is_dir() else ''}{meta}")
                        if entry.is_dir():
                            walk(entry, current_depth + 1, "")

            except PermissionError:
                output.append(f"{prefix}[Permission Denied]")

        walk(target, 1)
        return "\n".join(output)

    def search_files(self, root: str, name_pattern: str = None, content_match: str = None, max_results: int = 50) -> str:
        target = self._resolve_path(root)
        results =[]
        
        for root_dir, dirs, files in os.walk(target):
            default_ignore =[
                ".git", "node_modules", "node_module", "__pycache__", 
                ".next", "dist", "build", "built", "target", "out",
                "venv", ".venv", ".env", "env", "bin", "obj"
            ]
            dirs[:] = [d for d in dirs if d not in default_ignore]
            
            for file in files:
                if name_pattern and not fnmatch.fnmatch(file, name_pattern):
                    continue
                
                fp = Path(root_dir) / file
                
                if content_match:
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f):
                                if content_match in line:
                                    results.append(f"{fp}:{i+1}: {line.strip()[:200]}")
                                    if len(results) >= max_results: break
                    except: pass
                else:
                    results.append(str(fp))
                
                if len(results) >= max_results: break
            if len(results) >= max_results: break
            
        return "\n".join(results)

    def manage_file_system(self, action: str, src: str, dest: str = None, recursive: bool = False, force: bool = False) -> str:
        s = self._resolve_path(src)
        
        if action == "create_dir":
            try:
                s.mkdir(parents=True, exist_ok=True)
                return f"Success: Created directory {s}"
            except Exception as e: return f"Error creating directory: {e}"

        if not s.exists(): return f"Error: Source path {s} not found."

        d = None
        if action in["copy", "move", "rename"]:
            if not dest: return "Error: Destination path is required for copy/move/rename."
            d = self._resolve_path(dest)
            if d.exists() and not force:
                return f"Error: Destination {d} already exists. Set force=True to overwrite/merge."

        try:
            if action == "delete":
                if s.is_dir():
                    if recursive:
                        shutil.rmtree(s)
                    else:
                        try:
                            s.rmdir()
                        except OSError:
                            return "Error: Directory not empty. Set recursive=True to force delete."
                else:
                    s.unlink()
                return f"Success: Deleted {s}"

            elif action == "rename":
                if d.exists() and force:
                    if d.is_dir(): shutil.rmtree(d)
                    else: d.unlink()
                os.rename(s, d)
                return f"Success: Renamed {s} to {d}"
            
            elif action == "move":
                shutil.move(s, d)
                return f"Success: Moved {s} to {d}"
            
            elif action == "copy":
                if s.is_dir():
                    shutil.copytree(s, d, dirs_exist_ok=force)
                else:
                    shutil.copy2(s, d)
                return f"Success: Copied {s} to {d}"

        except Exception as e:
            return f"Error executing {action}: {e}"
        
        return f"Error: Unknown action '{action}'"