#!/usr/bin/env python3
"""
Hampi Battleground — Windows Background Task Monitor & Live Dashboard
Lightweight, native Windows-compatible task server with desktop notifications,
live terminal output, persistent history, and Unreal Engine build stage tracking.
"""

import os
import sys
import json
import time
import glob
import subprocess
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 7788
PROJECT_DIR = r"C:\UnrealProjects\Battleground"
MONITOR_DIR = os.path.join(PROJECT_DIR, "Tools", "TaskMonitor")
HISTORY_FILE = os.path.join(MONITOR_DIR, "task_history.json")
ANTIGRAVITY_TASKS_DIR = r"C:\Users\HP\.gemini\antigravity\brain\f1a3b3c6-c3fa-47d0-a85d-1c664ab2170b\.system_generated\tasks"
NOTIFY_SCRIPT = os.path.join(MONITOR_DIR, "notify.ps1")

os.makedirs(MONITOR_DIR, exist_ok=True)

# In-memory task registry
TASKS = {}
ACTIVE_PIDS = {}
TASKS_LOCK = threading.RLock()

def send_windows_notification(title, message, icon_type="Info"):
    """Fire a native Windows toast/balloon notification asynchronously."""
    def _run():
        try:
            if os.path.exists(NOTIFY_SCRIPT):
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-WindowStyle", "Hidden",
                    "-File", NOTIFY_SCRIPT,
                    "-Title", title,
                    "-Message", message,
                    "-IconType", icon_type
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except Exception as e:
            pass
    threading.Thread(target=_run, daemon=True).start()

def load_history():
    """Load persistent task history from JSON."""
    global TASKS
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                with TASKS_LOCK:
                    TASKS = saved
            print(f"[TaskMonitor] Loaded {len(TASKS)} historic tasks from {HISTORY_FILE}")
        except Exception as e:
            print(f"[TaskMonitor] Failed to load history: {e}")

def save_history():
    """Persist task history to JSON file."""
    with TASKS_LOCK:
        data = dict(TASKS)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[TaskMonitor] Error saving history: {e}")

def register_task(task_id, name, category="General", command="", working_dir=PROJECT_DIR, pid=None, notify=True):
    """Register a new task in the monitor."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task = {
        "id": task_id,
        "name": name,
        "category": category,
        "status": "RUNNING",
        "progress": 0,
        "stage": "Initializing...",
        "command": command,
        "working_dir": working_dir,
        "pid": pid,
        "start_time": now,
        "end_time": None,
        "duration_sec": 0,
        "log": f"[{now}] Task '{name}' started.\n",
        "error_message": None
    }
    with TASKS_LOCK:
        TASKS[task_id] = task
        if pid:
            ACTIVE_PIDS[task_id] = pid
    save_history()
    if notify:
        send_windows_notification("Task Started", f"{name} is now running.", "Info")
    return task

def update_task(task_id, progress=None, stage=None, status=None, append_log="", error_message=None, notify=True):
    """Update progress, status, or log of an active task."""
    with TASKS_LOCK:
        if task_id not in TASKS:
            return None
        task = TASKS[task_id]
        if progress is not None:
            task["progress"] = max(0, min(100, int(progress)))
        if stage:
            task["stage"] = stage
        if append_log:
            task["log"] += append_log
        if error_message:
            task["error_message"] = error_message
        if status:
            task["status"] = status
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                task["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    start_dt = datetime.strptime(task["start_time"], "%Y-%m-%d %H:%M:%S")
                    end_dt = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
                    task["duration_sec"] = int((end_dt - start_dt).total_seconds())
                except:
                    pass
                if notify:
                    if status == "COMPLETED":
                        task["progress"] = 100
                        send_windows_notification("Task Completed", f"{task['name']} finished successfully! ({task.get('duration_sec', 0)}s)", "Info")
                    elif status == "FAILED":
                        send_windows_notification("Task Failed", f"{task['name']} error: {error_message or 'See terminal'}", "Error")
                    elif status == "CANCELLED":
                        send_windows_notification("Task Cancelled", f"{task['name']} cancelled.", "Warning")
                if task_id in ACTIVE_PIDS:
                    del ACTIVE_PIDS[task_id]
    save_history()
    return task

def cancel_task(task_id):
    """Cancel a running task and terminate associated processes."""
    with TASKS_LOCK:
        if task_id not in TASKS:
            return False
        task = TASKS[task_id]
        pid = task.get("pid")
        if pid:
            try:
                subprocess.run(f"taskkill /PID {pid} /T /F", shell=True, capture_output=True)
            except Exception as e:
                print(f"[Cancel Error] {e}")
    update_task(task_id, status="CANCELLED", append_log=f"\n[{datetime.now().strftime('%H:%M:%S')}] Task cancelled by user.")
    return True

# Background scanner for Antigravity-spawned task logs
def antigravity_task_watcher():
    """Monitors .system_generated/tasks directory for task logs and tracks status."""
    time.sleep(2)
    seen_sizes = {}
    first_run = True
    while True:
        try:
            if os.path.exists(ANTIGRAVITY_TASKS_DIR):
                log_files = sorted(glob.glob(os.path.join(ANTIGRAVITY_TASKS_DIR, "task-*.log")), key=os.path.getmtime, reverse=True)[:15]
                for log_file in log_files:
                    fname = os.path.basename(log_file)
                    task_id = "agy-" + fname.replace(".log", "")
                    try:
                        sz = os.path.getsize(log_file)
                    except:
                        continue
                    mtime = os.path.getmtime(log_file)
                    now_ts = time.time()
                    
                    with TASKS_LOCK:
                        is_new = task_id not in TASKS
                    
                    if is_new:
                        t_name = f"Background Task ({fname})"
                        try:
                            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                                head = f.read(1500)
                                if "UnrealBuildTool" in head or "Build.bat" in head:
                                    t_name = "UBT C++ Compilation"
                                elif "setup_landscape" in head:
                                    t_name = "Landscape Setup"
                                elif "setup_navmesh" in head:
                                    t_name = "NavMesh & Level Setup"
                                elif "inspect_map" in head:
                                    t_name = "Level Inspector"
                                elif "-game" in head:
                                    t_name = "Game Simulation"
                        except:
                            pass
                        
                        task = register_task(task_id, t_name, category="Antigravity", command=log_file, working_dir=PROJECT_DIR, notify=(not first_run))
                        seen_sizes[log_file] = sz
                    else:
                        prev_sz = seen_sizes.get(log_file, 0)
                        if sz != prev_sz:
                            seen_sizes[log_file] = sz
                            try:
                                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                                    with TASKS_LOCK:
                                        if task_id in TASKS:
                                            TASKS[task_id]["log"] = content
                            except:
                                pass
                        
                        with TASKS_LOCK:
                            cur_status = TASKS.get(task_id, {}).get("status")
                        if cur_status == "RUNNING" and (now_ts - mtime > 5.0):
                            try:
                                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                                    tail = f.read()[-3000:]
                                    if "Command exited with code 0" in tail or "Success - 0 error(s)" in tail or "Total time in Parallel executor" in tail:
                                        update_task(task_id, status="COMPLETED", progress=100, stage="Finished", notify=(not first_run))
                                    elif "Command exited with code 1" in tail or "Fatal error:" in tail or "error C" in tail:
                                        update_task(task_id, status="FAILED", stage="Error", error_message="Build / Command Error detected in log", notify=(not first_run))
                                    elif "was canceled" in tail or "cancelled" in tail:
                                        update_task(task_id, status="CANCELLED", stage="Cancelled", notify=(not first_run))
                            except:
                                pass
                first_run = False
        except Exception as e:
            pass
        time.sleep(2)

# Embedded HTML Dashboard
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hampi Battleground — Task Monitor</title>
<style>
  :root {
    --bg-base: #18181c;
    --bg-card: #202026;
    --bg-hover: #292932;
    --border: #33333d;
    --accent: #007acc;
    --accent-hover: #1f8ad2;
    --success: #388e3c;
    --warning: #f57c00;
    --error: #d32f2f;
    --text-main: #e0e0e6;
    --text-dim: #90909e;
    --font-mono: Consolas, 'Courier New', monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: var(--bg-base);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  header {
    background: #121215;
    border-bottom: 1px solid var(--border);
    padding: 10px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 15px; }
  .brand .dot { width: 10px; height: 10px; border-radius: 50%; background: #4caf50; animation: pulse 2s infinite; }
  @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
  .stats-strip { display: flex; gap: 16px; font-size: 12px; color: var(--text-dim); }
  .stat-badge { background: var(--bg-card); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border); }
  .stat-badge b { color: var(--text-main); }
  
  .ue-stages {
    background: #16161a;
    padding: 8px 18px;
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }
  .stage-chip {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    background: #25252d;
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
  }
  .stage-chip.done { border-color: #2e7d32; color: #81c784; background: #1b3320; }
  .stage-chip.active { border-color: #0288d1; color: #4fc3f7; background: #102a3a; font-weight: 600; }

  .workspace {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  .left-pane {
    width: 440px;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
  }
  .pane-header {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .task-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .task-card {
    background: #1c1c22;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .task-card:hover { background: var(--bg-hover); border-color: #444452; }
  .task-card.selected { border-color: var(--accent); background: #182230; }
  .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .task-name { font-weight: 600; font-size: 13px; color: #fff; }
  .status-pill {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 10px;
    text-transform: uppercase;
  }
  .pill-RUNNING { background: #0277bd; color: #e1f5fe; animation: blink 1.5s infinite; }
  .pill-COMPLETED { background: #2e7d32; color: #e8f5e9; }
  .pill-FAILED { background: #c62828; color: #ffebee; }
  .pill-CANCELLED { background: #424242; color: #bdbdbd; }
  @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }

  .prog-track { background: #2c2c36; height: 5px; border-radius: 3px; overflow: hidden; margin: 6px 0; }
  .prog-fill { height: 100%; background: var(--accent); width: 0%; transition: width 0.3s; }
  .card-footer { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim); }
  .card-actions { display: flex; gap: 6px; margin-top: 6px; justify-content: flex-end; }
  .btn-sm {
    background: #2a2a34;
    border: 1px solid var(--border);
    color: var(--text-main);
    padding: 3px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11px;
  }
  .btn-sm:hover { background: #383846; }
  .btn-danger { color: #ef5350; border-color: #b71c1c; }
  .btn-danger:hover { background: #b71c1c; color: #fff; }

  .right-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #141416;
  }
  .term-toolbar {
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
    background: #1b1b20;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .term-view {
    flex: 1;
    padding: 12px;
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.5;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    color: #cfd8dc;
  }
  .line-err { color: #ff5252; font-weight: bold; }
  .line-warn { color: #ffd740; }
  .line-ok { color: #69f0ae; }
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="dot"></div>
    <span>HAMPI BATTLEGROUND — Background Task Monitor</span>
  </div>
  <div class="stats-strip">
    <div class="stat-badge">Active: <b id="stat-active">0</b></div>
    <div class="stat-badge">Completed: <b id="stat-done">0</b></div>
    <div class="stat-badge">Failed: <b id="stat-fail">0</b></div>
    <div class="stat-badge">Engine: <b>UE 5.4.4 (DX11)</b></div>
  </div>
</header>

<div class="ue-stages">
  <div class="stage-chip done"><span>✔</span> Phase 1: Level & Landscape Repair</div>
  <div class="stage-chip done"><span>✔</span> Phase 2: C++ Foundation (Battleground.exe)</div>
  <div class="stage-chip active"><span>⚙</span> Phase 3: Connected Hampi Regions</div>
  <div class="stage-chip"><span>○</span> Phase 4: Soldier & Weapons</div>
  <div class="stage-chip"><span>○</span> Phase 5: AI Bots & BR Zone</div>
  <div class="stage-chip"><span>○</span> Phase 6: Mobile Touch HUD</div>
  <div class="stage-chip"><span>○</span> Phase 7: Android ARM64 APK</div>
</div>

<div class="workspace">
  <div class="left-pane">
    <div class="pane-header">
      <span style="font-weight: 600;">Managed Tasks</span>
      <button class="btn-sm" onclick="fetchTasks()">↻ Refresh</button>
    </div>
    <div class="task-list" id="task-container">
      <div style="color: var(--text-dim); text-align: center; margin-top: 30px;">Loading tasks...</div>
    </div>
  </div>

  <div class="right-pane">
    <div class="term-toolbar">
      <span id="term-title" style="font-weight: 600;">Terminal Output</span>
      <div style="display: flex; gap: 8px;">
        <button class="btn-sm" onclick="openWorkingFolder()">📁 Open Folder</button>
        <button class="btn-sm" onclick="clearTerm()">Clear</button>
      </div>
    </div>
    <div class="term-view" id="terminal-content">// Select a task on the left to inspect its live logs and build output...</div>
  </div>
</div>

<script>
let tasksData = {};
let selectedTaskId = null;

async function fetchTasks() {
  try {
    const res = await fetch('/api/tasks');
    const data = await res.json();
    tasksData = data;
    renderTasks();
    updateStats();
    if (selectedTaskId && tasksData[selectedTaskId]) {
      renderLog(tasksData[selectedTaskId]);
    }
  } catch (e) {
    console.error("Fetch error:", e);
  }
}

function updateStats() {
  let active = 0, done = 0, fail = 0;
  Object.values(tasksData).forEach(t => {
    if (t.status === 'RUNNING') active++;
    else if (t.status === 'COMPLETED') done++;
    else if (t.status === 'FAILED') fail++;
  });
  document.getElementById('stat-active').innerText = active;
  document.getElementById('stat-done').innerText = done;
  document.getElementById('stat-fail').innerText = fail;
}

function renderTasks() {
  const container = document.getElementById('task-container');
  const items = Object.values(tasksData).reverse();
  if (items.length === 0) {
    container.innerHTML = '<div style="color: var(--text-dim); text-align: center; margin-top: 40px;">No background tasks recorded yet.</div>';
    return;
  }

  let html = '';
  items.forEach(t => {
    const isSel = (t.id === selectedTaskId);
    const cancelBtn = (t.status === 'RUNNING') 
      ? `<button class="btn-sm btn-danger" onclick="event.stopPropagation(); cancelTask('${t.id}')">Cancel</button>` 
      : '';
    html += `
      <div class="task-card ${isSel ? 'selected' : ''}" onclick="selectTask('${t.id}')">
        <div class="card-top">
          <span class="task-name">${t.name}</span>
          <span class="status-pill pill-${t.status}">${t.status}</span>
        </div>
        <div class="prog-track">
          <div class="prog-fill" style="width: ${t.progress}%;"></div>
        </div>
        <div class="card-footer">
          <span>${t.stage || t.category}</span>
          <span>${t.progress}% • ${t.duration_sec || 0}s</span>
        </div>
        <div class="card-actions">
          ${cancelBtn}
          <button class="btn-sm" onclick="event.stopPropagation(); openFolder('${t.id}')">📁 Folder</button>
        </div>
      </div>
    `;
  });
  container.innerHTML = html;

  if (!selectedTaskId && items.length > 0) {
    selectTask(items[0].id);
  }
}

function selectTask(id) {
  selectedTaskId = id;
  renderTasks();
  if (tasksData[id]) {
    renderLog(tasksData[id]);
  }
}

function renderLog(task) {
  document.getElementById('term-title').innerText = `${task.name} (PID: ${task.pid || 'N/A'}) — ${task.status}`;
  const term = document.getElementById('terminal-content');
  const raw = task.log || "// No log output recorded yet.";
  
  const lines = raw.split('\\n').map(line => {
    if (line.includes('error') || line.includes('Error') || line.includes('Fatal')) {
      return `<span class="line-err">${escapeHtml(line)}</span>`;
    } else if (line.includes('Warning') || line.includes('warn')) {
      return `<span class="line-warn">${escapeHtml(line)}</span>`;
    } else if (line.includes('Success') || line.includes('exited with code 0') || line.includes('Link [x64]')) {
      return `<span class="line-ok">${escapeHtml(line)}</span>`;
    }
    return escapeHtml(line);
  }).join('\\n');

  term.innerHTML = lines;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function clearTerm() {
  document.getElementById('terminal-content').innerHTML = '// Cleared';
}

async function cancelTask(id) {
  if (confirm(`Are you sure you want to cancel ${id}?`)) {
    await fetch(`/api/tasks/${id}/cancel`, { method: 'POST' });
    fetchTasks();
  }
}

async function openFolder(id) {
  await fetch(`/api/tasks/${id}/open_folder`, { method: 'POST' });
}

function openWorkingFolder() {
  if (selectedTaskId) {
    openFolder(selectedTaskId);
  }
}

setInterval(fetchTasks, 1500);
fetchTasks();
</script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/tasks":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with TASKS_LOCK:
                data = json.dumps(TASKS).encode("utf-8")
            self.wfile.write(data)
        elif parsed.path.startswith("/api/tasks/") and parsed.path.endswith("/log"):
            parts = parsed.path.strip("/").split("/")
            task_id = parts[2]
            with TASKS_LOCK:
                log_data = TASKS.get(task_id, {}).get("log", "No log found")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(log_data.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if "/cancel" in parsed.path:
            parts = parsed.path.strip("/").split("/")
            task_id = parts[2]
            success = cancel_task(task_id)
            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode("utf-8"))
        elif "/open_folder" in parsed.path:
            parts = parsed.path.strip("/").split("/")
            task_id = parts[2]
            with TASKS_LOCK:
                wdir = TASKS.get(task_id, {}).get("working_dir", PROJECT_DIR)
            subprocess.Popen(f'explorer.exe "{wdir}"', shell=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"opened"}')
        elif parsed.path == "/api/tasks/create":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            t = register_task(
                task_id=body.get("id", f"task_{int(time.time())}"),
                name=body.get("name", "Custom Task"),
                category=body.get("category", "General"),
                command=body.get("command", ""),
                working_dir=body.get("working_dir", PROJECT_DIR),
                pid=body.get("pid"),
                notify=True
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(t).encode("utf-8"))
        elif parsed.path == "/api/tasks/update":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            t = update_task(
                task_id=body.get("id"),
                progress=body.get("progress"),
                stage=body.get("stage"),
                status=body.get("status"),
                append_log=body.get("append_log", ""),
                error_message=body.get("error_message"),
                notify=True
            )
            self.send_response(200 if t else 404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(t or {}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def run_server():
    load_history()
    
    with TASKS_LOCK:
        if not TASKS:
            TASKS["task_01"] = {
                "id": "task_01",
                "name": "TASK 01: Project Foundation & C++ Build",
                "category": "Unreal C++",
                "status": "COMPLETED",
                "progress": 100,
                "stage": "Binaries Generated (Battleground.exe)",
                "command": "Build.bat Battleground Win64 Development",
                "working_dir": PROJECT_DIR,
                "pid": None,
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_sec": 137,
                "log": "Compile [x64] SharedPCH.Engine.Project.ValApi.Cpp20.cpp\\nCompile [x64] Battleground.cpp\\nLink [x64] Battleground.exe\\n[Success] 0 Errors, 0 Warnings.\\nExit code: 0",
                "error_message": None
            }
            save_history()

    server = ReusableHTTPServer(("127.0.0.1", PORT), RequestHandler)
    print(f"[TaskMonitor] Live Task Dashboard running at http://127.0.0.1:{PORT}", flush=True)

    watcher_thread = threading.Thread(target=antigravity_task_watcher, daemon=True)
    watcher_thread.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[TaskMonitor] Server stopped.", flush=True)

if __name__ == "__main__":
    run_server()
