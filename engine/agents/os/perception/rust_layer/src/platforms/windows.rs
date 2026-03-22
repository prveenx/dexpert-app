// FILE: /os/perception/rust_layer/src/platforms/windows.rs
#![allow(non_upper_case_globals)]
#![allow(unused_variables)]
#![allow(dead_code)]

use windows::{
    core::*, 
    Win32::Foundation::*,
    Win32::System::Com::*, 
    Win32::System::Ole::*,
    Win32::UI::Accessibility::*,
    Win32::UI::WindowsAndMessaging::*,
    Win32::Graphics::Dwm::*,
};
use crate::models::{UiNode, WindowInfo};
use std::sync::Mutex;
use std::collections::HashSet;
use std::time::{Instant, Duration};

lazy_static::lazy_static! {
    static ref WINDOW_LIST: Mutex<Vec<WindowInfo>> = Mutex::new(Vec::new());
}

pub struct UiaEngine {
    pub automation: IUIAutomation,
    pub cache_req: IUIAutomationCacheRequest,
    pub raw_walker: IUIAutomationTreeWalker,
}

trait SafeProperty {
    fn safe_name(&self) -> String;
    fn safe_help_text(&self) -> String;
    fn safe_control_type(&self) -> i32;
    fn safe_localized_control_type(&self) -> String;
    fn safe_is_enabled(&self) -> bool;
    fn safe_is_offscreen(&self) -> bool;
    fn safe_has_focus(&self) -> bool;
    fn safe_is_required(&self) -> bool;
    fn safe_is_valid(&self) -> bool;
    fn safe_rect(&self) -> (i32, i32, i32, i32);
    fn safe_runtime_id(&self) -> String;
    fn safe_class_name(&self) -> String;
    fn safe_automation_id(&self) -> String;
}

impl SafeProperty for IUIAutomationElement {
    fn safe_name(&self) -> String { unsafe { self.CachedName().unwrap_or_default().to_string() } }
    fn safe_help_text(&self) -> String { unsafe { self.CachedHelpText().unwrap_or_default().to_string() } }
    fn safe_control_type(&self) -> i32 { unsafe { self.CachedControlType().unwrap_or(windows::Win32::UI::Accessibility::UIA_CustomControlTypeId).0 as i32 } }
    fn safe_localized_control_type(&self) -> String { unsafe { self.CachedLocalizedControlType().unwrap_or_default().to_string() } }
    fn safe_is_enabled(&self) -> bool { unsafe { self.CachedIsEnabled().unwrap_or(TRUE).as_bool() } }
    fn safe_is_offscreen(&self) -> bool { unsafe { self.CachedIsOffscreen().unwrap_or(FALSE).as_bool() } }
    fn safe_has_focus(&self) -> bool { unsafe { self.CachedHasKeyboardFocus().unwrap_or(FALSE).as_bool() } }
    fn safe_is_required(&self) -> bool { unsafe { self.CachedIsRequiredForForm().unwrap_or(FALSE).as_bool() } }
    fn safe_is_valid(&self) -> bool { unsafe { self.CachedIsDataValidForForm().unwrap_or(TRUE).as_bool() } }
    fn safe_rect(&self) -> (i32, i32, i32, i32) {
        unsafe {
            let r = self.CachedBoundingRectangle().unwrap_or_default();
            (r.left, r.top, r.right - r.left, r.bottom - r.top)
        }
    }
    fn safe_runtime_id(&self) -> String {
        unsafe {
            match self.GetRuntimeId() {
                Ok(rid) => {
                    let mut result = String::new();
                    let mut p_data = std::ptr::null_mut();
                    if SafeArrayAccessData(rid, &mut p_data).is_ok() {
                        if let (Ok(lower), Ok(upper)) = (SafeArrayGetLBound(rid, 1), SafeArrayGetUBound(rid, 1)) {
                            let count = (upper - lower + 1) as usize;
                            let data = std::slice::from_raw_parts(p_data as *const i32, count);
                            result = data.iter().map(|i| i.to_string()).collect::<Vec<_>>().join("-");
                        }
                        let _ = SafeArrayUnaccessData(rid);
                    }
                    if result.is_empty() { format!("{:?}", rid) } else { result }
                },
                Err(_) => "no_rid".to_string()
            }
        }
    }
    fn safe_class_name(&self) -> String { unsafe { self.CachedClassName().unwrap_or_default().to_string() } }
    fn safe_automation_id(&self) -> String { unsafe { self.CachedAutomationId().unwrap_or_default().to_string() } }
}

unsafe extern "system" fn enum_window_callback(hwnd: HWND, _: LPARAM) -> BOOL {
    if !IsWindowVisible(hwnd).as_bool() { return TRUE; }
    
    // Skip Windows 10/11 "Cloaked" UWP background windows
    let mut cloaked = 0u32;
    if DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, &mut cloaked as *mut _ as *mut std::ffi::c_void, 4).is_ok() {
        if cloaked != 0 { return TRUE; }
    }

    let mut rect = RECT::default();
    if GetWindowRect(hwnd, &mut rect).is_err() { return TRUE; }
    if (rect.right - rect.left) <= 10 || (rect.bottom - rect.top) <= 10 { return TRUE; }

    let mut text:[u16; 512] = [0; 512];
    let len = GetWindowTextW(hwnd, &mut text);
    let mut class_buf: [u16; 256] =[0; 256];
    let class_len = GetClassNameW(hwnd, &mut class_buf);
    let class_name = String::from_utf16_lossy(&class_buf[..class_len as usize]);
    let mut title = String::new();

    if len > 0 {
        title = String::from_utf16_lossy(&text[..len as usize]);
    } else if class_name == "Shell_TrayWnd" || class_name == "Shell_SecondaryTrayWnd" {
        title = "Windows Taskbar".to_string();
    }

    if !title.is_empty() && title != "Program Manager" && title != "Microsoft Text Input Application" {
         let mut process_id = 0;
         GetWindowThreadProcessId(hwnd, Some(&mut process_id));
         WINDOW_LIST.lock().unwrap().push(WindowInfo {
            handle: hwnd.0,
            title,
            process_id,
            class_name,
        });
    }
    TRUE
}

impl UiaEngine {
    pub fn new() -> Result<Self> {
        unsafe {
            CoInitializeEx(None, COINIT_MULTITHREADED).ok();
            let automation: IUIAutomation = CoCreateInstance(&CUIAutomation, None, CLSCTX_INPROC_SERVER)?;
            let cache_req = automation.CreateCacheRequest()?;
            
            cache_req.AddProperty(UIA_NamePropertyId)?;
            cache_req.AddProperty(UIA_BoundingRectanglePropertyId)?;
            cache_req.AddProperty(UIA_ControlTypePropertyId)?;
            cache_req.AddProperty(UIA_IsEnabledPropertyId)?;
            cache_req.AddProperty(UIA_IsOffscreenPropertyId)?;
            cache_req.AddProperty(UIA_AutomationIdPropertyId)?;
            cache_req.AddProperty(UIA_ClassNamePropertyId)?;
            cache_req.AddProperty(UIA_LocalizedControlTypePropertyId)?;
            cache_req.AddProperty(UIA_HelpTextPropertyId)?;
            cache_req.AddProperty(UIA_HasKeyboardFocusPropertyId)?;
            
            cache_req.AddPattern(UIA_InvokePatternId)?; 
            cache_req.AddPattern(UIA_TogglePatternId)?; 
            cache_req.AddPattern(UIA_ValuePatternId)?;
            cache_req.AddPattern(UIA_SelectionItemPatternId)?;
            cache_req.AddPattern(UIA_ExpandCollapsePatternId)?; 
            cache_req.AddPattern(UIA_ScrollPatternId)?; 
            cache_req.AddPattern(UIA_TextPatternId)?; 
            cache_req.AddPattern(UIA_LegacyIAccessiblePatternId)?;

            cache_req.SetTreeScope(TreeScope_Element)?; 
            
            // 🚀 THE ELECTRON CONQUEROR: RawViewWalker forces Chromium to yield nodes that it hides from standard walkers
            let raw_walker = automation.RawViewWalker()?;

            Ok(UiaEngine { automation, cache_req, raw_walker })
        }
    }

    unsafe fn process_element(
        &self, 
        element: &IUIAutomationElement, 
        depth: usize, 
        start_time: Instant, 
        root_rect: (i32, i32, i32, i32),
        visited: &mut HashSet<String>
    ) -> Option<UiNode> {
        if start_time.elapsed() > Duration::from_secs(20) { return None; }
        if depth > 100 { return None; } 

        let (x, y, w, h) = element.safe_rect();
        let control_id = element.safe_control_type();
        let role_str_base = self.map_control_type(control_id);

        // Exterminate Scrollbars and purely decorative elements immediately
        if role_str_base == "SCL" || role_str_base == "SEP" || role_str_base == "THM" {
            return None;
        }

        // 🚀 SMART VIEWPORT CULLING FOR ELECTRON
        // We use a massive 800px buffer to ensure we don't accidentally cull virtualized list items (WhatsApp chats)
        let (rx, ry, rw, rh) = root_rect;
        if rw > 0 && rh > 0 && depth > 2 {
            let buf = 800; 
            if x > (rx + rw + buf) || (x + w) < (rx - buf) || y > (ry + rh + buf) || (y + h) < (ry - buf) {
                return None; 
            }
        }
        
        let rid = element.safe_runtime_id();
        
        // 🚀 AGGRESSIVE DEDUPLICATION FIX
        // Chromium often returns the exact same RuntimeId for siblings. We must composite the key with spatial data.
        let dedup_key = format!("{}|{}|{}|{}|{}|{}", rid, role_str_base, x, y, w, h);
        if !visited.insert(dedup_key) { return None; }

        let mut name = element.safe_name();
        if name.is_empty() {
            name = element.safe_help_text();
        }

        let mut value_str: Option<String> = None;
        let is_text_role = matches!(role_str_base.as_str(), "EDIT" | "INP" | "DOC" | "CUST");
        let mut text_found = false;

        // 1. Try Cached ValuePattern
        if let Ok(pattern) = element.GetCachedPattern(UIA_ValuePatternId) {
            if let Ok(vp) = pattern.cast::<IUIAutomationValuePattern>() {
                if let Ok(val) = vp.CachedValue() {
                    let v = val.to_string();
                    if !v.is_empty() { value_str = Some(v); text_found = true; }
                }
            }
        }

        // 2. Try Live ValuePattern / TextPattern for heavy documents/code editors
        if !text_found || is_text_role {
            if let Ok(pattern) = element.GetCurrentPattern(UIA_ValuePatternId) {
                if let Ok(vp) = pattern.cast::<IUIAutomationValuePattern>() {
                    if let Ok(val) = vp.CurrentValue() {
                        let mut v = val.to_string();
                        if !v.is_empty() {
                            if v.len() > 10000 { v = format!("{} ... [TRUNCATED - MASSIVE FILE]", &v[..8000]); }
                            value_str = Some(v);
                            text_found = true;
                        }
                    }
                }
            }

            if !text_found {
                if let Ok(pattern) = element.GetCachedPattern(UIA_TextPatternId) {
                    if let Ok(tp) = pattern.cast::<IUIAutomationTextPattern>() {
                        if let Ok(range) = tp.DocumentRange() {
                            if let Ok(text) = range.GetText(10001) {
                                let mut t = text.to_string();
                                if !t.is_empty() {
                                    if t.len() > 10000 {
                                        t = format!("{} ... [TRUNCATED - MASSIVE FILE]", &t[..8000]);
                                    }
                                    value_str = Some(t);
                                }
                            }
                        }
                    }
                }
            }
        }

        // Fallback to Legacy IAccessible
        if let Ok(pattern) = element.GetCachedPattern(UIA_LegacyIAccessiblePatternId) {
            if let Ok(legacy) = pattern.cast::<IUIAutomationLegacyIAccessiblePattern>() {
                if name.is_empty() {
                    if let Ok(n) = legacy.CachedName() {
                        let n_str = n.to_string();
                        if !n_str.is_empty() { name = n_str; }
                    }
                }
                if let Ok(v) = legacy.CachedValue() {
                    let v_str = v.to_string();
                    if !v_str.is_empty() && value_str.is_none() { 
                        value_str = Some(v_str); 
                    }
                }
            }
        }

        if let Some(ref v) = value_str {
            let n_lower = name.to_lowercase();
            let v_lower = v.to_lowercase();
            let labels = ["name", "date modified", "type", "size", "status"];
            if labels.contains(&n_lower.as_str()) && !labels.contains(&v_lower.as_str()) { name = v.clone(); }
        }
        if name.is_empty() {
            if let Some(ref v) = value_str { name = v.clone(); }
        }

        // 🚀 DYNAMIC ROLE INFERENCING
        // Fixes React/Electron generic divs behaving as buttons/checkboxes
        let has_invoke = element.GetCachedPattern(UIA_InvokePatternId).and_then(|p| p.cast::<IUIAutomationInvokePattern>()).is_ok();
        let has_toggle = element.GetCachedPattern(UIA_TogglePatternId).and_then(|p| p.cast::<IUIAutomationTogglePattern>()).is_ok();
        let has_selection = element.GetCachedPattern(UIA_SelectionItemPatternId).and_then(|p| p.cast::<IUIAutomationSelectionItemPattern>()).is_ok();

        let mut actual_role = role_str_base.clone();
        if (has_invoke || has_toggle || has_selection) && matches!(actual_role.as_str(), "CUST" | "GRP" | "PANE" | "TXT" | "IMG" | "UNK") {
            if has_toggle {
                actual_role = "CHK".to_string();
            } else if has_selection {
                actual_role = "ITEM".to_string();
            } else {
                actual_role = "BTN".to_string();
            }
        }

        // --- STATE EXTRACTION ---
        let mut states = Vec::new();
        let mut scroll_percent = -1.0;
        let mut explicit_scrollable = false;

        if !element.safe_is_enabled() { states.push("[DISABLED]".to_string()); }
        if element.safe_has_focus() { states.push("[FOCUSED]".to_string()); }
        
        if let Ok(pattern) = element.GetCachedPattern(UIA_ExpandCollapsePatternId) {
            if let Ok(expand) = pattern.cast::<IUIAutomationExpandCollapsePattern>() {
                if let Ok(state) = expand.CachedExpandCollapseState() {
                    if state == ExpandCollapseState_Expanded { states.push("[EXPANDED]".to_string()); }
                    else if state == ExpandCollapseState_Collapsed { states.push("[COLLAPSED]".to_string()); }
                }
                if !states.contains(&"[HAS_MENU]".to_string()) { states.push("[HAS_MENU]".to_string()); }
            }
        }
        if actual_role == "SEL" && !states.contains(&"[HAS_MENU]".to_string()) {
            states.push("[HAS_MENU]".to_string());
        }

        if has_toggle {
            if let Ok(pattern) = element.GetCachedPattern(UIA_TogglePatternId) {
                if let Ok(toggle) = pattern.cast::<IUIAutomationTogglePattern>() {
                    if let Ok(state) = toggle.CachedToggleState() {
                        if state == ToggleState_On { states.push("[ON]".to_string()); }
                        else if state == ToggleState_Off { states.push("[OFF]".to_string()); }
                    }
                }
            }
        }

        if has_selection {
            if let Ok(pattern) = element.GetCachedPattern(UIA_SelectionItemPatternId) {
                if let Ok(sel) = pattern.cast::<IUIAutomationSelectionItemPattern>() {
                    if sel.CachedIsSelected().unwrap_or(FALSE).as_bool() {
                        states.push("[SELECTED]".to_string());
                    }
                }
            }
        }

        if let Ok(pattern) = element.GetCachedPattern(UIA_ScrollPatternId) {
            if let Ok(scroll) = pattern.cast::<IUIAutomationScrollPattern>() {
                let v = scroll.CachedVerticallyScrollable().unwrap_or(FALSE).as_bool();
                let h = scroll.CachedHorizontallyScrollable().unwrap_or(FALSE).as_bool();
                if v || h {
                     explicit_scrollable = true;
                     states.push("[SCROLLABLE]".to_string());
                     if v { scroll_percent = scroll.CachedVerticalScrollPercent().unwrap_or(-1.0); }
                }
            }
        }

        let mut children = Vec::new();
        
        // 🚀 THE ELECTRON CONQUEROR: Walk the raw view manually.
        // FindAllBuildCache outright fails on complex WebViews across process boundaries.
        let mut child_opt = self.raw_walker.GetFirstChildElementBuildCache(element, &self.cache_req).ok();
        while let Some(child) = child_opt {
            if let Some(node) = self.process_element(&child, depth + 1, start_time, root_rect, visited) {
                children.push(node);
            }
            child_opt = self.raw_walker.GetNextSiblingElementBuildCache(&child, &self.cache_req).ok();
        }

        // --- Inside UiaEngine::process_element ---
        let mut is_scrollable = explicit_scrollable;
        if !is_scrollable && !children.is_empty() && h > 20 {
            // 🚀 FIX: Prevent React flexbox overflow from turning UI buttons/items into false scrollables
            if matches!(actual_role.as_str(), "PANE" | "GRP" | "ZONE" | "DOC" | "LIST" | "TBL" | "TREE" | "DAT") {
                let mut max_y = 0;
                let mut min_y = 100000;
                for child in &children {
                    if child.bbox[1] < min_y { min_y = child.bbox[1]; }
                    if (child.bbox[1] + child.bbox[3]) > max_y { max_y = child.bbox[1] + child.bbox[3]; }
                }
                let content_height = max_y - min_y;
                
                // 🚀 FIX: Enforce a strict 50px buffer. Fractional CSS pixels won't trigger it anymore.
                if content_height > (h + 50) {
                    is_scrollable = true;
                    if !states.contains(&"[SCROLLABLE]".to_string()) { states.push("[SCROLLABLE]".to_string()); }
                }
            }
        }

        Some(UiNode {
            id: element.safe_runtime_id(),
            name: name.trim().to_string(),
            role: actual_role,
            localized_role: element.safe_localized_control_type(), 
            states,
            value: value_str,
            description: None, help_text: None, item_status: None,
            bbox: [x, y, w, h],
            children,
            automation_id: element.safe_automation_id(),
            class_name: element.safe_class_name(),
            is_scrollable, scroll_percent, is_expanded: false, is_draggable: false,
        })
    }

    pub fn map_control_type(&self, id: i32) -> String {
        match id {
            50000 => "BTN", 50001 => "CAL", 50002 => "CHK", 50003 => "SEL",
            50004 => "INP", 50005 => "LNK", 50006 => "IMG", 50007 => "ITEM",
            50008 => "LIST", 50009 => "MNU", 50010 => "MNU", 50011 => "ITEM",
            50012 => "PROG", 50013 => "RAD", 50014 => "SCL", 50015 => "SLD",
            50016 => "SPN", 50017 => "STAT", 50018 => "TAB", 50019 => "TABI",
            50020 => "TXT", 50021 => "TBR", 50022 => "TIP", 50023 => "TREE",
            50024 => "ITEM", 50025 => "CUST", 50026 => "GRP", 50027 => "THM",
            50028 => "DAT", 50029 => "ITEM", 50030 => "DOC", 50031 => "BTN",
            50032 => "WIN", 50033 => "PANE", 50034 => "HDR", 50035 => "HDRI",
            50036 => "TBL", 50037 => "TTL", 50038 => "SEP",
            _ => "UNK",
        }.to_string()
    }
}

pub fn list_active_windows() -> std::result::Result<Vec<WindowInfo>, String> {
    unsafe {
        WINDOW_LIST.lock().unwrap().clear();
        EnumWindows(Some(enum_window_callback), LPARAM(0)).ok();
        let list = WINDOW_LIST.lock().unwrap();
        Ok(list.clone())
    }
}

pub fn focus_window(window_id: &str) -> std::result::Result<String, String> {
    unsafe {
        if let Ok(hwnd) = window_id.parse::<isize>() {
            let handle = HWND(hwnd);
            if IsIconic(handle).as_bool() { ShowWindow(handle, SW_RESTORE); }
            SetForegroundWindow(handle);
            return Ok("Window Focused by Handle".to_string());
        }
        Err("Invalid Window ID".to_string())
    }
}

pub fn scan_focused_window(window_id: &str) -> std::result::Result<serde_json::Value, String> {
    unsafe {
        let mut hwnd = GetForegroundWindow();
        if !window_id.is_empty() {
            if let Ok(h) = window_id.parse::<isize>() {
                hwnd = HWND(h);
            }
        }

        if hwnd.0 == 0 { return Err("No active window to scan.".to_string()); }

        let engine = UiaEngine::new().map_err(|e: windows::core::Error| e.to_string())?;
        
        let root_element = match engine.automation.ElementFromHandleBuildCache(hwnd, &engine.cache_req) {
            Ok(elem) => elem,
            Err(_) => engine.automation.ElementFromHandle(hwnd).map_err(|e| e.to_string())?
        };

        let root_rect = root_element.safe_rect();
        let mut visited = HashSet::new();

        let tree = engine.process_element(&root_element, 0, Instant::now(), root_rect, &mut visited)
            .ok_or("Failed to traverse UIA tree")?;
        
        Ok(serde_json::to_value(&tree).unwrap())
    }
}

pub fn click_element(ax_id: i32) -> std::result::Result<(), String> {
    Err("Handled by Python PyAutoGUI now".to_string())
}
pub fn launch_app(_query: &str) -> std::result::Result<(), String> {
    Err("Handled by Python".to_string())
}