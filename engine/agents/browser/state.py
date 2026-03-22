# FILE: /browser/state.py
import base64
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    
    def center(self) -> Dict[str, float]:
        return {"x": self.x + (self.width / 2), "y": self.y + (self.height / 2)}

class DOMNode(BaseModel):
    ax_id: int
    role: str
    name: str = ""
    value: Optional[str] = None
    states: List[str] = Field(default_factory=list)
    bbox: BoundingBox
    selector: Optional[str] = None 
    xpath: Optional[str] = None    
    attributes: Dict[str, Any] = Field(default_factory=dict) 
    is_shadow_root: bool = False

    model_config = ConfigDict(extra='ignore')

    def to_string_rep(self) -> str:
        # COMPACT REPRESENTATION: [ID] ROLE "Name" {STATES} [EXTRA]
        
        # 1. ID & Role (Shortened)
        base = f"[{self.ax_id}] {self.role}"
        
        # 2. Name & Value (Aggressive Truncation)
        name_clean = (self.name or "").replace('\n', ' ').strip()
        if len(name_clean) > 40: name_clean = name_clean[:37] + "..."
        
        val_clean = (self.value or "").replace('\n', ' ').strip()
        if len(val_clean) > 30: val_clean = val_clean[:27] + "..."
        
        content = f' "{name_clean}"' if name_clean else ""
        if val_clean and val_clean != name_clean:
            content += f" (Val:{val_clean})"
            
        # 3. States (Filtered)
        # Keep only critical states to reduce noise
        critical_states = {'[CHECKED]', '[DISABLED]', '[EXPANDED]', '[SELECTED]', '[UPLOAD]', '[DOWNLOAD]'}
        active_states = [s for s in self.states if s in critical_states]
        state_str = " " + "".join(active_states) if active_states else ""
        
        # 4. Attributes (HREF / SRC)
        attr_str = ""
        if self.role in ("LINK", "A") and "href" in self.attributes:
            href = self.attributes["href"]
            # Ignore javascript: and purely internal anchors
            if href and len(href) > 5 and not href.startswith("javascript"):
                if len(href) > 40: href = href[:37] + "..."
                attr_str = f" -> {href}"
        
        return f"{base}{content}{state_str}{attr_str}"

class BrowserTab(BaseModel):
    page_id: int
    title: str
    url: str
    is_active: bool

class DownloadTask(BaseModel):
    id: str
    filename: str
    status: str
    downloaded_mb: float = 0.0
    total_mb: float = 0.0
    percent: float = 0.0
    speed_mb_s: float = 0.0
    elapsed_seconds: int = 0
    eta_seconds: int = -1
    final_path: Optional[str] = None
    error: Optional[str] = None

    model_config = ConfigDict(extra='ignore')

class BrowserState(BaseModel):
    url: str
    title: str
    tabs: List[BrowserTab] = Field(default_factory=list)
    downloads: List[DownloadTask] = Field(default_factory=list)
    dom_nodes: Dict[int, DOMNode] = Field(default_factory=dict)
    screenshot_base64: Optional[str] = None
    viewport_size: Dict[str, int] = Field(default_factory=dict)
    scan_duration_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)

    def get_node(self, ax_id: int) -> Optional[DOMNode]:
        return self.dom_nodes.get(ax_id)

    def get_element_by_fuzzy_text(self, text: str) -> Optional[DOMNode]:
        text = text.lower()
        for node in self.dom_nodes.values():
            if text in node.name.lower():
                return node
        return None

    def prompt_representation(self) -> str:
        lines =[]
        
        # 🚀 SOTA: Rich Download Output showing ETA and Percentage for the LLM
        if self.downloads:
            lines.append("--- DOWNLOADS ---")
            for d in self.downloads:
                if d.status == "downloading":
                    eta_str = f"ETA: {d.eta_seconds}s" if d.eta_seconds >= 0 else "ETA: Unknown"
                    total_str = f" / {d.total_mb:.1f}MB" if d.total_mb > 0 else ""
                    pct_str = f"{int(d.percent)}% " if d.total_mb > 0 else ""
                    lines.append(
                        f" ⏳ {d.filename} [task_id={d.id}] - "
                        f"{pct_str}({d.downloaded_mb:.1f}MB{total_str}) @ {d.speed_mb_s:.1f}MB/s | {eta_str}"
                    )
                elif d.status == "completed":
                    lines.append(f" ✅ {d.filename}[task_id={d.id}] → {d.final_path}")
                elif d.status == "failed":
                    lines.append(f" ❌ {d.filename} [task_id={d.id}] FAILED: {d.error}")
            lines.append("-" * 20)

        # 2. DOM Tree
        lines.append("INTERACTIVE ELEMENTS:")
        
        # Sort spatially
        sorted_nodes = sorted(self.dom_nodes.values(), key=lambda n: (n.bbox.y, n.bbox.x))
        
        # TOKEN SAVER: Filter heavily populated trees
        # If > 300 nodes, strip generic structural nodes that have no text/value
        if len(sorted_nodes) > 300:
            lines.append("(Tree compressed: Showing interactive/text nodes only)")
            filtered =[]
            for n in sorted_nodes:
                is_interactive = n.role in ('BTN', 'INP', 'LINK', 'CHK', 'TAB', 'MENU', 'SELECT')
                has_content = (n.name and len(n.name) > 2) or n.value
                if is_interactive or has_content:
                    filtered.append(n)
            sorted_nodes = filtered

        for node in sorted_nodes:
            lines.append(node.to_string_rep())
            
        return "\n".join(lines)