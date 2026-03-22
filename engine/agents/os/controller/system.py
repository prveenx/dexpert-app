import platform
import os
import psutil
import socket
from typing import List, Dict, Union, Optional

class SystemController:
    def get_system_info(self, categories: List[str] = ["all"], include_apps: bool = False) -> Dict[str, Union[str, Dict]]:
        info = {}
        all_cats = "all" in categories
        
        if all_cats or "cpu" in categories:
            info["cpu"] = {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=0.1),
                "freq": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
            }
            
        if all_cats or "memory" in categories:
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent
            }
            
        if all_cats or "disk" in categories:
            disk = psutil.disk_usage('/')
            info["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
            
        if all_cats or "network" in categories:
            net = psutil.net_io_counters()
            info["network"] = {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
                "hostname": socket.gethostname()
            }
            
        if all_cats or "env" in categories:
            info["env"] = dict(os.environ)

        if all_cats or "user" in categories:
            info["user"] = {
                "name": os.getlogin() if hasattr(os, 'getlogin') else "unknown",
                "home": os.path.expanduser('~'),
                "cwd": os.getcwd(),
                "os": platform.system(),
                "version": platform.version(),
                "machine": platform.machine()
            }
            
        if include_apps:
            # On-demand: Retrieval of installed apps can be slow
            apps = []
            if platform.system() == "Windows":
                 # Fast way: Check Start Menu shortcuts
                 start_menu = [
                     os.path.join(os.environ.get('ProgramData', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
                     os.path.join(os.environ.get('AppData', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
                 ]
                 for path in start_menu:
                     if os.path.exists(path):
                         for root, dirs, files in os.walk(path):
                             for f in files:
                                 if f.endswith('.lnk'):
                                     app_name = f.rsplit('.', 1)[0]
                                     if app_name not in apps: apps.append(app_name)
                             if len(apps) > 100: break
            else:
                 # Linux/Mac: Check /usr/share/applications or /Applications
                 paths = ["/usr/share/applications", "/Applications"]
                 for p in paths:
                     if os.path.exists(p):
                         apps.extend(os.listdir(p)[:50])
            info["apps"] = apps[:100]

        if all_cats or "processes" in categories:
            # Listing processes can be heavy, limit to top 50
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
                try:
                    p_info = p.info
                    # Memory in MB
                    p_info['memory_mb'] = p_info['memory_info'].rss / (1024 * 1024) if p_info.get('memory_info') else 0
                    del p_info['memory_info']
                    procs.append(p_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if len(procs) >= 50: break
            info["processes"] = sorted(procs, key=lambda x: x.get('memory_mb', 0), reverse=True)
            
        return info

    def manage_process(self, action: str, filter: str = None, signal_str: str = "SIGTERM") -> str:
        if action == "list":
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'status']):
                 if filter:
                     if str(p.info['pid']) == filter or filter in p.info['name']:
                         procs.append(p.info)
                 else:
                     procs.append(p.info)
            return str(procs[:50])

        elif action == "kill":
            killed = []
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    should_kill = False
                    if filter:
                        if str(p.info['pid']) == filter or filter in p.info['name']:
                            should_kill = True
                    
                    if should_kill:
                        p.terminate() 
                        killed.append(f"{p.info['name']} ({p.info['pid']})")
                except psutil.AccessDenied:
                    killed.append(f"Failed to kill {p.info['pid']} (Access Denied)")
                except Exception as e:
                    killed.append(f"Error killing {p.info['pid']}: {e}")
            return f"Killed: {', '.join(killed)}"
            
        elif action == "get_info":
             # Implementation similar to list but more details
             pass
        
        return "Action not implemented or invalid."
