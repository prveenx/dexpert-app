// FILE: /os/perception/rust_layer/src/platforms/linux.rs
#![cfg(target_os = "linux")]

use crate::models::WindowInfo;
use serde_json::{json, Value};
use atspi::accessible::{AccessibleProxy, Role};
use atspi::component::ComponentProxy;
use zbus::Connection;
use std::time::{Instant, Duration};

pub fn list_active_windows() -> Result<Vec<WindowInfo>, String> {
    // wmctrl is the standard for X11/XWayland window management
    let output = std::process::Command::new("wmctrl")
        .arg("-l").output().map_err(|e| e.to_string())?;
        
    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut windows = Vec::new();
    
    for line in stdout.lines() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() > 3 {
            let title = parts[3..].join(" ");
            // Use the hex ID directly as the string handle for wmctrl compatibility
            windows.push(WindowInfo {
                handle: 0, 
                title: format!("[ID: {}] {}", parts[0], title),
                process_id: 0,
                class_name: "X11Window".to_string()
            });
        }
    }
    Ok(windows)
}

pub fn focus_window(window_id: &str) -> Result<String, String> {
    // Extract Hex ID if passed in the format we generated
    let id_clean = window_id.split(']').next().unwrap_or(window_id).replace("[ID: ", "");
    
    std::process::Command::new("wmctrl")
        .arg("-i").arg("-a").arg(id_clean.trim())
        .output().map_err(|e| e.to_string())?;
    Ok(format!("Focused: {}", window_id))
}

pub fn launch_app(query: &str) -> Result<(), String> {
    std::process::Command::new("setsid").arg(query).spawn().map_err(|e| e.to_string())?;
    Ok(())
}

// Tokio bridge for async zbus execution
pub fn scan_focused_window(_window_id: &str) -> Result<Value, String> {
    let rt = tokio::runtime::Runtime::new().map_err(|e| e.to_string())?;
    rt.block_on(async_scan())
}

async fn async_scan() -> Result<Value, String> {
    let conn = Connection::session().await.map_err(|e| e.to_string())?;
    
    // AT-SPI Registry - get the desktop
    let desktop_proxy = AccessibleProxy::builder(&conn)
        .destination("org.a11y.atspi.Registry")
        .map_err(|e| e.to_string())?
        .path("/org/a11y/atspi/accessible/root")
        .map_err(|e| e.to_string())?
        .build().await.map_err(|e| e.to_string())?;

    // Find the Active/Focused App
    let mut active_app_proxy = None;
    if let Ok(children) = desktop_proxy.get_children().await {
        for child_ref in children {
            if let Ok(app_proxy) = AccessibleProxy::builder(&conn)
                .destination(child_ref.name.clone())
                .unwrap().path(child_ref.path.clone()).unwrap()
                .build().await {
                
                // Check if this app has the active state
                if let Ok(state_set) = app_proxy.get_state().await {
                    // State 1 is usually Active/Focused in AT-SPI
                    if state_set.contains(atspi::State::Active) || state_set.contains(atspi::State::Focused) {
                        active_app_proxy = Some(app_proxy);
                        break;
                    }
                }
            }
        }
    }

    if let Some(app) = active_app_proxy {
        let tree = crawl_atspi(&conn, &app, 0, Instant::now()).await;
        Ok(tree.unwrap_or_else(|| json!({"role": "WIN", "name": "Empty Window", "children": []})))
    } else {
        Err("No focused application found on AT-SPI bus.".to_string())
    }
}

async fn crawl_atspi(conn: &Connection, proxy: &AccessibleProxy<'_>, depth: usize, start: Instant) -> Option<Value> {
    if start.elapsed() > Duration::from_secs(10) || depth > 50 { return None; }

    let name = proxy.name().await.unwrap_or_default();
    let role = proxy.get_role().await.unwrap_or(Role::Unknown);
    
    // Attempt to get BBox via Component interface
    let mut bbox = [0, 0, 0, 0];
    if let Ok(comp) = ComponentProxy::builder(conn)
        .destination(proxy.destination()).unwrap()
        .path(proxy.path()).unwrap()
        .build().await {
        
        if let Ok(extents) = comp.get_extents(0).await {
            bbox = [extents.0, extents.1, extents.2, extents.3];
        }
    }

    let role_str = match role {
        Role::PushButton | Role::ToggleButton => "BTN",
        Role::Text | Role::Entry | Role::PasswordText => "EDIT",
        Role::Label => "TXT",
        Role::Link => "LNK",
        Role::CheckBox => "CHK",
        Role::RadioButton => "RAD",
        Role::Image | Role::Icon => "IMG",
        Role::List => "LIST",
        Role::ListItem => "ITEM",
        Role::Table => "TBL",
        Role::TableRow => "ROW",
        Role::Window | Role::Frame => "WIN",
        Role::Panel | Role::ScrollPane => "PANE",
        _ => "UNK",
    };

    let mut children_json = Vec::new();
    if let Ok(children) = proxy.get_children().await {
        for child_ref in children {
            if let Ok(child_proxy) = AccessibleProxy::builder(conn)
                .destination(child_ref.name.clone()).unwrap()
                .path(child_ref.path.clone()).unwrap()
                .build().await {
                
                if let Some(c_node) = crawl_atspi(conn, &child_proxy, depth + 1, start).await {
                    children_json.push(c_node);
                }
            }
        }
    }

    Some(json!({
        "id": "",
        "name": name,
        "role": role_str,
        "localized_role": format!("{:?}", role),
        "states": [],
        "value": None::<String>,
        "bbox": bbox,
        "children": children_json,
        "automation_id": "",
        "class_name": "",
        "is_scrollable": role == Role::ScrollPane,
        "scroll_percent": -1.0,
        "is_expanded": false,
        "is_draggable": false,
    }))
}