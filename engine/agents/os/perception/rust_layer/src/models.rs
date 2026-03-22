// FILE: /os/perception/rust_layer/src/models.rs
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct UiNode {
    // Core Identifiers
    pub id: String,
    pub name: String,
    pub role: String,
    pub localized_role: String,
    
    // Content & State
    pub states: Vec<String>,
    pub value: Option<String>,
    pub description: Option<String>,
    pub help_text: Option<String>,
    pub item_status: Option<String>,
    
    // Geometry: [x, y, width, height]
    pub bbox: [i32; 4], 
    
    // Hierarchy
    pub children: Vec<UiNode>,
    
    // OS-Specific Metadata
    pub automation_id: String,
    pub class_name: String,
    
    // Spatial/Interaction hints
    pub is_scrollable: bool,
    pub scroll_percent: f64,
    pub is_expanded: bool,
    pub is_draggable: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct WindowInfo {
    pub handle: isize,
    pub title: String,
    pub process_id: u32,
    pub class_name: String,
}