# FILE: /browser/tools/models.py
"""
Pydantic schemas for every tool the Browser Agent can call.

The LLM outputs JSON matching these models inside an [ACTION] block.
Each model carries a fixed `tool_name` literal so the registry can
route it to the correct handler.

Design note: the agent is allowed to output **multiple** actions per
turn (e.g., type into a field + click submit).  The registry iterates
through the list and executes them sequentially.
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class BrowserBaseTool(BaseModel):
    """Marker base for all browser tool schemas."""
    pass


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

class NavigateAction(BrowserBaseTool):
    """Navigates to a specific URL."""
    tool_name: Literal["go_to_url"] = "go_to_url"
    url: str = Field(..., description="Full URL to navigate to (e.g. https://google.com).")


class GoBackAction(BrowserBaseTool):
    """Navigates back in browser history."""
    tool_name: Literal["go_back"] = "go_back"


class RefreshAction(BrowserBaseTool):
    """Reloads the current page."""
    tool_name: Literal["refresh"] = "refresh"


class SwitchTabAction(BrowserBaseTool):
    """Switches to a tab by its zero-based index."""
    tool_name: Literal["switch_tab"] = "switch_tab"
    tab_index: int = Field(..., description="Zero-based index of the target tab.")


class CloseTabAction(BrowserBaseTool):
    """Closes a tab by its zero-based index. If no index is provided, closes the active tab."""
    tool_name: Literal["close_tab"] = "close_tab"
    tab_index: Optional[int] = Field(None, description="Optional zero-based index of the target tab to close.")


# ---------------------------------------------------------------------------
# Interaction
# ---------------------------------------------------------------------------

class ClickAction(BrowserBaseTool):
    """Clicks an interactive element by its Accessibility ID."""
    tool_name: Literal["click_element"] = "click_element"
    target_id: str = Field(..., description="The ax-ID from the semantic tree (e.g. 'ax-42').")


class InputTextAction(BrowserBaseTool):
    """Types text into an input field."""
    tool_name: Literal["input_text"] = "input_text"
    target_id: str = Field(..., description="The ax-ID of the input field.")
    text: str = Field(..., description="The text to type.")
    submit: bool = Field(False, description="Press Enter after typing.")


class SelectDropdownAction(BrowserBaseTool):
    """Selects a value from a <select> dropdown element."""
    tool_name: Literal["select_option"] = "select_option"
    target_id: str = Field(..., description="ax-ID of the <select> element.")
    value: str = Field(..., description="The visible text or value attribute of the option.")


class HoverAction(BrowserBaseTool):
    """Hovers over an element to reveal hidden menus or tooltips."""
    tool_name: Literal["hover"] = "hover"
    target_id: str = Field(..., description="ax-ID of the element to hover.")


class ScrollAction(BrowserBaseTool):
    """Scrolls the page."""
    tool_name: Literal["scroll"] = "scroll"
    direction: Literal["up", "down", "top", "bottom"] = Field("down")
    amount: Optional[int] = Field(None, description="Pixels to scroll (default 500).")


class KeyPressAction(BrowserBaseTool):
    """Sends a keyboard shortcut (e.g., Escape, Tab, Enter)."""
    tool_name: Literal["key_press"] = "key_press"
    key: str = Field(..., description="Key name: Enter, Escape, Tab, ArrowDown, etc.")


class WaitAction(BrowserBaseTool):
    """Pauses execution to allow page to update."""
    tool_name: Literal["wait"] = "wait"
    seconds: float = Field(2.0, description="Seconds to wait.")

    # ---------------------------------------------------------------------------
    # Download Management
    # ---------------------------------------------------------------------------

class WaitForDownloadAction(BrowserBaseTool):
    """
    TRUE POLLER: Suspends your execution and polls continuously until a background
    download is 100% complete (or fails). Unlike 'wait', this does NOT return
    after a fixed time — it blocks until the download finishes.
    
    Accepts either the UUID task_id OR the filename (e.g., 'CursorUserSetup-x64-2.6.12.exe').
    """
    tool_name: Literal["wait_for_download"] = "wait_for_download"
    task_id: str = Field(..., description="The task UUID from DOWNLOAD_STARTED, OR the filename (e.g., 'app.exe'). Both work.")
    timeout: float = Field(600.0, description="Maximum seconds to wait before giving up (default 10 minutes).")

class CancelDownloadAction(BrowserBaseTool):
    """
    Cancels an active background download task if it is no longer needed.
    """
    tool_name: Literal["cancel_download"] = "cancel_download"
    task_id: str = Field(..., description="The background task ID to cancel.")

class AskClarificationAction(BrowserBaseTool):
    """
    Stops execution to ask the Manager (Planner) for missing information 
    (e.g., credentials, specific search terms, 2FA codes).
    """
    tool_name: Literal["ask_clarification"] = "ask_clarification"
    question: str = Field(..., description="The specific question you need answered to proceed.")
    context: Optional[str] = Field(None, description="Why do you need this?")


# ---------------------------------------------------------------------------
# Vision (on-demand, cost-guarded)
# ---------------------------------------------------------------------------

class AnalyzeVisualAction(BrowserBaseTool):
    """
    Sends the current viewport (or a cropped region) to the Vision LLM.

    Use cases:
      - Read CAPTCHA / distorted text
      - Describe a chart or image the DOM cannot represent
      - Find elements missing from the semantic tree

    Note: Vision is OFF by default for cost efficiency.
    This tool explicitly activates a one-shot screenshot + Vision LLM call.
    """
    tool_name: Literal["analyze_visual"] = "analyze_visual"
    query: str = Field(
        ...,
        description="What to look for, e.g. 'Read the CAPTCHA text', 'Describe the chart'.",
    )
    target_id: Optional[str] = Field(
        None,
        description="If provided (e.g. 'ax-42'), crop screenshot to this element's bounding box + padding.",
    )
    focus_box: Optional[List[int]] = Field(
        None,
        description="Manual crop [x, y, width, height] when target_id is unavailable.",
    )


# ---------------------------------------------------------------------------
# Scratchpad (data persistence across pages)
# ---------------------------------------------------------------------------

class ScratchpadSaveAction(BrowserBaseTool):
    """Save extracted data or notes to the agent's volatile scratchpad."""
    tool_name: Literal["scratchpad_save"] = "scratchpad_save"
    data: Dict[str, Any] = Field(..., description="Key-value data to persist.")
    target_id: Optional[str] = Field(None, description="The ax-ID of the container this data came from (enables auto-image capture).")
    note: Optional[str] = Field(None, description="Optional human-readable note.")


class ScratchpadEnqueueAction(BrowserBaseTool):
    """Add items to the scratchpad processing queue. Pass ax_id for auto URL extraction."""
    tool_name: Literal["scratchpad_enqueue"] = "scratchpad_enqueue"
    items: Optional[List[Dict[str, Any]]] = Field(None, description="Items to enqueue: [{title: 'Name', ax_id: 'ax-42'}, ...]. The system auto-extracts real URLs from ax_ids.")
    urls: Optional[List[str]] = Field(None, description="(Fallback) URLs to add to the queue.")


class ScratchpadReadAction(BrowserBaseTool):
    """Read current scratchpad state (queue, collected data, progress)."""
    tool_name: Literal["scratchpad_read"] = "scratchpad_read"


# ---------------------------------------------------------------------------
# Extraction (workflow trigger)
# ---------------------------------------------------------------------------

class ExtractionAction(BrowserBaseTool):
    """Triggers the multi-page extraction workflow (Gather→Process→Report)."""
    tool_name: Literal["start_extraction"] = "start_extraction"
    instruction: str = Field(..., description="What to extract, e.g. 'Get all coffee shops with name and rating'.")
    max_items: int = Field(10, description="Maximum items to collect before stopping.")

# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------

class TaskCompleteAction(BrowserBaseTool):
    """Signals that the user's goal has been achieved."""
    tool_name: Literal["task_complete"] = "task_complete"
    summary: str = Field(..., description="Concise summary of the result.")