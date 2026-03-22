# FILE: /os/tools/models.py
from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator

# --- File System Tools ---

class ReadFileInput(BaseModel):
    tool_name: Literal["read_file"] = "read_file"
    path: str = Field(..., description="Absolute path to the file.")
    range: Optional[Dict[str, int]] = Field(None, description="Line range {start, end} or byte range.")
    format: Literal["auto", "pdf"] = Field("auto", description="File format. 'auto'/ 'pdf' will attempt to extract text from PDF files.")
    extract: Optional[str] = Field(None, description="Structured extraction query (e.g., JSONPath, CSV columns).")
    encoding: str = "utf-8"
    max_lines: Optional[int] = Field(None, description="Maximum number of lines to read.")
    truncation_strategy: Literal["smart", "head", "tail", "middle"] = "smart"
    search_hint: Optional[str] = Field(None, description="Keyword/Regex to find relevant section if truncating.")

class WriteFileInput(BaseModel):
    tool_name: Literal["write_file"] = "write_file"
    path: str = Field(..., description="Absolute path to the file.")
    content: str = Field(..., description="Content to write.")
    mode: Literal["overwrite", "append"] = "overwrite"
    create_parents: bool = True
    encoding: str = "utf-8"

class EditFileInput(BaseModel):
    tool_name: Literal["edit_file"] = "edit_file"
    path: str = Field(..., description="Absolute path to the file to edit.")
    operations: List[Dict[str, str]] = Field(
        ..., 
        description="List of edit operations. Format:[{'type': 'search_replace', 'search': 'EXACT block of existing code', 'replace': 'new code block to insert'}]."
    )
    dry_run: bool = False
    allow_multiple_matches: bool = Field(False, description="Set True to replace all instances of the search block.")

class ListDirInput(BaseModel):
    tool_name: Literal["list_dir"] = "list_dir"
    path: str = Field(..., description="Directory path.")
    depth: Union[int, str] = Field(2, description="Traversal depth. -1 for recursive. Can be string '1', '2', etc.")
    tree: bool = False
    ignore: Union[List[str], str] = Field(default_factory=list, description="Patterns to ignore. Can be a list or a comma-separated string.")
    include_hidden: bool = False
    filter: Optional[str] = Field(None, description="Glob or extension filter.")
    show_meta: bool = False

    @field_validator("ignore", mode="before")
    @classmethod
    def validate_ignore(cls, v):
        if v is None or v == "" or v == "None":
            return[]
        if isinstance(v, str):
            return [pref.strip() for pref in v.split(",") if pref.strip()]
        return v

    @field_validator("depth", mode="before")
    @classmethod
    def validate_depth(cls, v):
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v

class SearchFilesInput(BaseModel):
    tool_name: Literal["search_files"] = "search_files"
    root: str = Field(..., description="Root directory to search.")
    name_pattern: Optional[str] = None
    content_match: Optional[str] = None
    file_types: Optional[Union[List[str], str]] = None
    context_lines: int = 2
    max_results: int = 50
    ignore: Union[List[str], str] = Field(default_factory=list)

    @field_validator("ignore", "file_types", mode="before")
    @classmethod
    def validate_lists(cls, v):
        if v is None or v == "" or v == "None":
            return []
        if isinstance(v, str):
            return[pref.strip() for pref in v.split(",") if pref.strip()]
        return v

class ManageFileSystemInput(BaseModel):
    tool_name: Literal["manage_file_system"] = "manage_file_system"
    action: Literal["copy", "move", "delete", "rename", "create_dir"] = Field(..., description="Action to perform. Use 'copy', 'move', 'delete', 'rename', or 'create_dir'. NOTE: For listing files, use 'list_dir' instead.")
    src: str = Field(..., description="Source path (or directory to create).")
    dest: Optional[str] = Field(None, description="Destination path (for copy, move, rename).")
    recursive: bool = False
    force: bool = False

# --- Execution Tools ---

class ExecuteScriptInput(BaseModel):
    tool_name: Literal["execute_script"] = "execute_script"
    language: Literal["python", "powershell", "bash", "cmd", "shell"] = Field(..., description="Language. Use 'shell' for simple commands (mkdir, echo, git, etc).")
    code: str = Field(..., description="Script content or command line.")
    cwd: Optional[str] = Field(None, description="Working directory.")
    env: Optional[Dict[str, str]] = None
    timeout: float = Field(30.0, description="Max wait time. If blocking=False, this is the initial wait.")
    blocking: bool = Field(False, description="If True, wait for completion. If False, return task_id.")
    context: Optional[Dict[str, Any]] = None

class CheckStatusInput(BaseModel):
    tool_name: Literal["check_status"] = "check_status"
    pid: Optional[int] = None
    task_id: Optional[str] = None
    wait: float = 0.0

class WaitInput(BaseModel):
    tool_name: Literal["wait"] = "wait"
    seconds: int = Field(..., description="Seconds to pause.")
    reason: Optional[str] = None

# --- System Tools ---

class GetSystemInfoInput(BaseModel):
    tool_name: Literal["get_system_info"] = "get_system_info"
    categories: Union[List[str], str] = Field(
        default_factory=lambda:["user"],
        description="Core categories to retrieve. 'user' includes identity/OS info."
    )
    include_apps: bool = Field(False, description="On-demand: Scan for installed applications (heavy operation).")

    @field_validator("categories", mode="before")
    @classmethod
    def validate_categories(cls, v):
        if v is None or v == "" or v == "None":
            return ["user"]
        if isinstance(v, str):
            return[pref.strip() for pref in v.split(",") if pref.strip()]
        return v

class ManageProcessInput(BaseModel):
    tool_name: Literal["manage_process"] = "manage_process"
    action: Literal["list", "kill", "get_info"] = "list"
    filter: Optional[str] = Field(None, description="pid/name/cmd pattern")
    signal: str = "SIGTERM"

# --- Network Tools ---

class HttpRequestInput(BaseModel):
    tool_name: Literal["http_request"] = "http_request"
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"] = "GET"
    url: str = Field(..., description="URL.")
    headers: Optional[Dict[str, str]] = None
    body: Optional[Union[str, Dict[str, Any]]] = None
    timeout: float = 10.0
    follow_redirects: bool = True
    extract: Optional[str] = None
    response_format: Literal["auto", "json", "text"] = "auto"

# ===================================================================
# MACRO OS MANAGEMENT (Global State & Windows)
# ===================================================================

class ListWindowsInput(BaseModel):
    tool_name: Literal["list_windows"] = "list_windows"

class FocusWindowInput(BaseModel):
    tool_name: Literal["focus_window"] = "focus_window"
    window_id: Union[str, int] = Field(..., description="The ID of the window.")

    @field_validator("window_id", mode="before")
    def force_string(cls, v):
        return str(v)

class LaunchAppInput(BaseModel):
    tool_name: Literal["launch_app"] = "launch_app"
    query: str = Field(..., description="The name of the application to search and launch natively (e.g., 'notepad', 'chrome', 'calculator').")

# ===================================================================
# MICRO OS INTERACTION (Focused Window Controls)
# ===================================================================

class ScanWindowInput(BaseModel):
    tool_name: Literal["scan_window"] = "scan_window"
    continuous: bool = Field(False, description="If True, activates Live UI Tracking. The agent will automatically see the foreground window on every future step without needing to call scan_window again.")

class ClickElementInput(BaseModel):
    tool_name: Literal["click_element"] = "click_element"
    ax_id: str = Field(..., description="The ID of the element from the semantic tree (e.g., '14' or 'ax-14').")
    click_type: Literal["left", "right", "double", "middle"] = Field("left", description="Type of mouse click.")

class InputTextInput(BaseModel):
    tool_name: Literal["input_text"] = "input_text"
    ax_id: str = Field(..., description="The ID of the text field to type into.")
    text: str = Field(..., description="The string to type.")
    submit: bool = Field(False, description="If True, presses 'Enter' immediately after typing.")

class PressKeyInput(BaseModel):
    tool_name: Literal["press_key"] = "press_key"
    key_combo: str = Field(..., description="Keyboard shortcuts (e.g., 'enter', 'tab', 'escape', 'ctrl+c', 'win').")

class ScrollInput(BaseModel):
    tool_name: Literal["scroll"] = "scroll"
    direction: Literal["up", "down", "left", "right"] = Field("down", description="Direction to scroll.")
    amount: int = Field(5, description="Number of scroll ticks/lines.")
    target_id: Optional[str] = Field(None, description="If scrolling a specific pane, provide its ax_id.")

class DragAndDropInput(BaseModel):
    tool_name: Literal["drag_and_drop"] = "drag_and_drop"
    source_id: str = Field(..., description="The ax_id of the item to grab.")
    dest_id: str = Field(..., description="The ax_id of the drop target.")

class AnalyzeVisualInput(BaseModel):
    tool_name: Literal["analyze_visual"] = "analyze_visual"
    query: str = Field(..., description="What to look for visually.")
    target_id: Optional[str] = Field(None, description="Crops the screenshot to this specific element.")
    focus_box: Optional[Union[List[int], str]] = Field(None, description="manual crop coordinates [x, y, w, h].")

    @field_validator("focus_box", mode="before")
    @classmethod
    def validate_focus_box(cls, v):
        if v is None or v == "" or v == "None":
            return None
        if isinstance(v, str):
            try:
                # Handle "[x, y, w, h]" or "x, y, w, h"
                cleaned = v.strip("[]").replace(" ", "")
                return[int(x) for x in cleaned.split(",")]
            except:
                return None
        return v