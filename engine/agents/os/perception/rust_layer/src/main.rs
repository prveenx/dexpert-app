mod platforms; // Imports macos.rs, linux.rs, windows.rs based on target_os
pub mod models; 

use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

fn main() -> anyhow::Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    // Handshake
    println!("{}", json!({"status": "ready"}));
    io::stdout().flush().ok();

    let stdin = io::stdin();
    for line_result in stdin.lock().lines() {
        let line = match line_result {
            Ok(l) => l.trim().to_string(),
            Err(_) => break,
        };
        
        if line.is_empty() { continue; }

        let req: Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(e) => {
                send_error(&format!("Invalid JSON: {}", e));
                continue;
            }
        };

        let action = req["action"].as_str().unwrap_or("unknown");

        match action {
            "list_windows" => {
                match platforms::list_active_windows() {
                    Ok(windows) => send_success(json!({"windows": windows})),
                    Err(e) => send_error(&e),
                }
            }
            "focus_window" => {
                let window_id = req["window_id"].as_str().unwrap_or("");
                match platforms::focus_window(window_id) {
                    Ok(title) => send_success(json!({"title": title})),
                    Err(e) => send_error(&e),
                }
            }
            "launch_app" => {
                let query = req["query"].as_str().unwrap_or("");
                match platforms::launch_app(query) {
                    Ok(_) => send_success(json!({"status": "launched"})),
                    Err(e) => send_error(&e),
                }
            }
            "scan_active" => {
                let window_id = req["window_id"].as_str().unwrap_or("");
                // platforms::scan_focused_window now returns raw JSON across all OSes
                match platforms::scan_focused_window(window_id) {
                    Ok(tree_json) => {
                        send_success(json!({
                            "semantic_tree": tree_json
                        }))
                    },
                    Err(e) => send_error(&e),
                }
            }
            // Fallbacks if Python doesn't want to use PyAutoGUI
            "get_coordinates" => send_error("Use Python PyAutoGUI cache instead."),
            "click_element" => send_error("Use Python PyAutoGUI click instead."),
            "exit" => break,
            _ => send_error(&format!("Unknown action: {}", action)),
        }
    }
    Ok(())
}

fn send_success(data: Value) {
    let out = serde_json::to_string(&data).unwrap_or_else(|_| "{}".to_string());
    println!("{}", out);
    io::stdout().flush().ok();
}

fn send_error(msg: &str) {
    let err = json!({ "error": msg });
    println!("{}", err);
    io::stdout().flush().ok();
}