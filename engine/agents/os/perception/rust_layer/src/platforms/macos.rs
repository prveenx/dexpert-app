// FILE: /os/perception/rust_layer/src/platforms/macos.rs
#![cfg(target_os = "macos")]

use crate::models::WindowInfo;
use core_foundation::base::{TCFType, TCFTypeRef};
use core_foundation::string::{CFString, CFStringRef};
use core_foundation::array::CFArray;
use core_graphics::geometry::{CGPoint, CGSize};
use accessibility_sys::{
    kAXChildrenAttribute, kAXRoleAttribute, kAXTitleAttribute, kAXValueAttribute, 
    kAXPositionAttribute, kAXSizeAttribute, kAXFocusedApplicationAttribute, 
    kAXIdentifierAttribute, AXUIElementCreateSystemWide, AXUIElementCopyAttributeValue, 
    AXUIElementRef, AXValueRef, kAXValueTypeCGPoint, kAXValueTypeCGSize, AXValueGetValue
};
use serde_json::{json, Value};
use std::ffi::c_void;
use std::ptr;
use std::time::{Instant, Duration};

struct AxElement(AXUIElementRef);

impl AxElement {
    fn system_wide() -> Self {
        unsafe { AxElement(AXUIElementCreateSystemWide()) }
    }

    fn get_attribute<T: TCFType>(&self, attribute: CFStringRef) -> Option<T> {
        unsafe {
            let mut value: *const c_void = ptr::null();
            if AXUIElementCopyAttributeValue(self.0, attribute, &mut value) == 0 && !value.is_null() {
                Some(T::wrap_under_get_rule(value as *mut _))
            } else {
                None
            }
        }
    }

    fn get_string(&self, attribute: CFStringRef) -> String {
        self.get_attribute::<CFString>(attribute).map(|s| s.to_string()).unwrap_or_default()
    }

    fn get_children(&self) -> Vec<AxElement> {
        unsafe {
            if let Some(array) = self.get_attribute::<CFArray>(kAXChildrenAttribute) {
                array.into_iter().map(|ptr| AxElement(ptr as AXUIElementRef)).collect()
            } else {
                vec![]
            }
        }
    }

    fn get_bbox(&self) -> [i32; 4] {
        unsafe {
            let mut x = 0.0; let mut y = 0.0; let mut w = 0.0; let mut h = 0.0;

            let mut pos_val: *const c_void = ptr::null();
            if AXUIElementCopyAttributeValue(self.0, kAXPositionAttribute, &mut pos_val) == 0 {
                let mut point = CGPoint::default();
                AXValueGetValue(pos_val as AXValueRef, kAXValueTypeCGPoint, &mut point as *mut _ as *mut c_void);
                x = point.x; y = point.y;
            }

            let mut size_val: *const c_void = ptr::null();
            if AXUIElementCopyAttributeValue(self.0, kAXSizeAttribute, &mut size_val) == 0 {
                let mut size = CGSize::default();
                AXValueGetValue(size_val as AXValueRef, kAXValueTypeCGSize, &mut size as *mut _ as *mut c_void);
                w = size.width; h = size.height;
            }

            [x as i32, y as i32, w as i32, h as i32]
        }
    }
}

pub fn list_active_windows() -> Result<Vec<WindowInfo>, String> {
    // AppleScript is safest for fetching user-facing window lists on macOS
    let output = std::process::Command::new("osascript")
        .arg("-e").arg("tell application \"System Events\" to get name of every process whose background only is false")
        .output().map_err(|e| e.to_string())?;
        
    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut windows = Vec::new();
    
    for (i, name) in stdout.split(',').enumerate() {
        let title = name.trim().to_string();
        if !title.is_empty() {
            windows.push(WindowInfo { handle: i as isize, title, process_id: 0, class_name: "MacApp".into() });
        }
    }
    Ok(windows)
}

pub fn focus_window(window_id: &str) -> Result<String, String> {
    // Focus using AppleScript
    let script = format!("tell application \"{}\" to activate", window_id);
    std::process::Command::new("osascript").arg("-e").arg(&script).output().map_err(|e| e.to_string())?;
    Ok(format!("Focused: {}", window_id))
}

pub fn launch_app(query: &str) -> Result<(), String> {
    std::process::Command::new("open").arg("-a").arg(query).spawn().map_err(|e| e.to_string())?;
    Ok(())
}

pub fn scan_focused_window(_window_id: &str) -> Result<Value, String> {
    unsafe {
        let system = AxElement::system_wide();
        
        // Grab the actively focused app
        let app_elem_ref = system.get_attribute::<core_foundation::base::TCFTypeRef>(kAXFocusedApplicationAttribute)
            .ok_or("No focused application found via AX API")?;
            
        let app = AxElement(app_elem_ref.as_concrete_TypeRef() as AXUIElementRef);
        
        // Crawl
        let tree_json = crawl_element(&app, 0, Instant::now())
            .unwrap_or_else(|| json!({"role": "WIN", "name": "Empty Window", "children": []}));
            
        Ok(tree_json)
    }
}

unsafe fn crawl_element(element: &AxElement, depth: usize, start: Instant) -> Option<Value> {
    if start.elapsed() > Duration::from_secs(10) || depth > 50 { return None; }

    let raw_role = element.get_string(kAXRoleAttribute);
    let name = element.get_string(kAXTitleAttribute);
    let value = element.get_string(kAXValueAttribute);
    let auto_id = element.get_string(kAXIdentifierAttribute);
    let bbox = element.get_bbox();

    // Map Mac Roles to PCAgent Roles
    let role = match raw_role.as_str() {
        "AXButton" | "AXPopUpButton" => "BTN",
        "AXTextField" | "AXTextArea" => "EDIT",
        "AXStaticText" => "TXT",
        "AXLink" => "LNK",
        "AXCheckBox" => "CHK",
        "AXRadioButton" => "RAD",
        "AXImage" => "IMG",
        "AXList" | "AXOutline" => "LIST",
        "AXTable" => "TBL",
        "AXRow" => "ROW",
        "AXWindow" => "WIN",
        "AXGroup" | "AXScrollArea" => "PANE",
        _ => "UNK",
    };

    let mut children = Vec::new();
    for child in element.get_children() {
        if let Some(child_node) = crawl_element(&child, depth + 1, start) {
            children.push(child_node);
        }
    }

    Some(json!({
        "id": "",
        "name": name,
        "role": role,
        "localized_role": raw_role,
        "states": [],
        "value": if value.is_empty() { None::<String> } else { Some(value) },
        "bbox": bbox,
        "children": children,
        "automation_id": auto_id,
        "class_name": "",
        "is_scrollable": raw_role == "AXScrollArea",
        "scroll_percent": -1.0,
        "is_expanded": false,
        "is_draggable": false,
    }))
}