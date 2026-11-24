#!/usr/bin/env python3
"""
CLI wrapper to execute any command while streaming live progress,
status, and logs to the Hampi Battleground Task Monitor.
Usage:
  python run_task.py --name "Compile C++" --category "Build" --cmd "Build.bat ..."
"""

import sys
import json
import argparse
import subprocess
import urllib.request
import re

MONITOR_API = "http://127.0.0.1:7788/api/tasks"

def notify_monitor(endpoint, data):
    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=1.5) as res:
            return json.loads(res.read().decode("utf-8"))
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description="Run command with visible dashboard tracking")
    parser.add_argument("--name", required=True, help="Display name of the task")
    parser.add_argument("--category", default="Build", help="Category name")
    parser.add_argument("--cmd", required=True, help="Command line to execute")
    parser.add_argument("--cwd", default=r"C:\UnrealProjects\Battleground", help="Working directory")
    args = parser.parse_args()

    task_id = f"task_{abs(hash(args.name + args.cmd)) % 1000000}"

    print(f"=== Starting Task: {args.name} ===")
    print(f"Command: {args.cmd}")

    # Register task
    notify_monitor(f"{MONITOR_API}/create", {
        "id": task_id,
        "name": args.name,
        "category": args.category,
        "command": args.cmd,
        "working_dir": args.cwd
    })

    # Start process
    proc = subprocess.Popen(
        args.cmd,
        cwd=args.cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    notify_monitor(f"{MONITOR_API}/update", {
        "id": task_id,
        "pid": proc.pid
    })

    full_log = []
    total_actions = None

    for line in iter(proc.stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()
        full_log.append(line)

        # Parse Unreal progress e.g. [1/14] Compile ...
        match = re.search(r"\[(\d+)/(\d+)\]\s+(.*)", line)
        progress = None
        stage = None
        if match:
            cur = int(match.group(1))
            total = int(match.group(2))
            progress = int((cur / total) * 100)
            stage = match.group(3).strip()

        notify_monitor(f"{MONITOR_API}/update", {
            "id": task_id,
            "progress": progress,
            "stage": stage,
            "append_log": line
        })

    proc.stdout.close()
    return_code = proc.wait()

    status = "COMPLETED" if return_code == 0 else "FAILED"
    err = None if return_code == 0 else f"Process exited with code {return_code}"

    notify_monitor(f"{MONITOR_API}/update", {
        "id": task_id,
        "status": status,
        "progress": 100 if return_code == 0 else None,
        "stage": "Finished" if return_code == 0 else "Failed",
        "error_message": err
    })

    print(f"=== Task Finished with Exit Code: {return_code} ({status}) ===")
    sys.exit(return_code)

if __name__ == "__main__":
    main()
