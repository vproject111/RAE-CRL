#!/usr/bin/env python3
"""
RAE Session Bootstrap Script (Smart Black Box Connector)
======================================================
MANDATORY STARTUP STEP.
Dependency-free version (uses standard library only).
Forces "RAE-First" by INJECTING active memory context directly into stdout.
"""

import sys
import json
import os
import urllib.request
import urllib.error
import socket
import uuid

# --- Configuration ---
DEFAULT_URL = "http://localhost:8001"
LUMINA_URL = "http://100.68.166.117:8001"
LITE_URL = "http://localhost:8008"
SESSION_FILE = ".rae_session"

# Standard headers
HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-Id": "default-tenant"
}

def get_or_create_session_id():
    """Maintains session continuity across bootstrap calls."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            sid = f.read().strip()
            if sid:
                return sid
    
    new_sid = str(uuid.uuid4())
    with open(SESSION_FILE, "w") as f:
        f.write(new_sid)
    return new_sid

def make_request(url, method='GET', data=None, timeout=5):
    """Robust HTTP request using standard library."""
    try:
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None

        req = urllib.request.Request(url, data=data_bytes, headers=HEADERS, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"error": str(e)}
    except urllib.error.URLError as e:
        return 0, {"error": str(e.reason)}
    except socket.timeout:
        return 0, {"error": "timeout"}
    except Exception as e:
        return 0, {"error": str(e)}

def get_active_url():
    """Finds the working RAE API URL."""
    print("🔍 Probing RAE Nodes...")
    # Prioritize Stable Node 1 (Lumina) over potentially broken Local Dev
    urls = [LUMINA_URL, DEFAULT_URL, LITE_URL]
    
    for url in urls:
        print(f"   Target: {url} ... ", end="", flush=True)
        code, _ = make_request(f"{url}/health", timeout=1)
        if code == 200:
            print("ONLINE ✅")
            return url
        print("OFFLINE ❌")
    return None

def fetch_black_box_context(base_url):
    """Pulls the latest mental state from RAE."""
    print(f"\n🧠 ACCESSING HIVE MIND via {base_url}...")
    
    # 1. Fetch Working Memory (Immediate Context)
    query_payload = {
        "query_text": "Current session goals, active tasks, and recent critical fixes",
        "k": 5,
        "layers": ["working", "episodic"]
    }
    
    code, data = make_request(f"{base_url}/v1/memory/query", method='POST', data=query_payload)
    
    if code == 200:
        results = data.get("results", [])
        print("\n=== 📂 ACTIVE CONTEXT (FROM RAE) ===")
        if not results:
            print("(No recent context found. Starting fresh?)")
        for item in results:
            content = item.get("content") or item.get("text")
            layer = item.get("layer", "unknown")
            print(f"[{layer.upper()}] {content[:200]}..." if len(content) > 200 else f"[{layer.upper()}] {content}")
    else:
        print(f"⚠️  Memory Query Failed: {code}")

    # 2. Fetch Strategic Directives (Reflective)
    query_payload["layers"] = ["reflective", "semantic"]
    query_payload["query_text"] = "Strategic protocols, critical stability rules"
    
    code, data = make_request(f"{base_url}/v1/memory/query", method='POST', data=query_payload)
    
    if code == 200:
        results = data.get("results", [])
        print("\n=== 🛡️  PROTOCOL DIRECTIVES ===")
        for item in results:
            content = item.get("content") or item.get("text")
            print(f"> {content}")

def log_session_start(base_url, session_id):
    """Automatically creates a memory trace that a new session has started."""
    import getpass
    import platform
    
    user = getpass.getuser()
    node = platform.node()
    
    payload = {
        "content": f"RAE-First Session Activated. User: {user} | Node: {node} | Protocol: HARD_FRAMES_V1",
        "layer": "working",
        "importance": 0.2,
        "tags": ["session-start", "rae-first", "implicit-capture"],
        "source": "bootstrap_script",
        "session_id": session_id
    }
    
    # Fire and forget
    make_request(f"{base_url}/v1/memory/store", method='POST', data=payload)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAE Bootstrap")
    parser.add_argument("--node", type=str, choices=["local", "node1"], default="local", help="Node to connect to")
    args = parser.parse_args()

    session_id = get_or_create_session_id()
    print(f"🔌 RAE-First Bootstrap (Node: {args.node.upper()})...")
    print(f"🆔 SESSION_ID: {session_id}")
    
    if args.node == "node1":
        active_url = LUMINA_URL
    else:
        # Check Local Dev first, then Lite
        active_url = None
        for url in [DEFAULT_URL, LITE_URL]:
            code, _ = make_request(f"{url}/health", timeout=1)
            if code == 200:
                active_url = url
                break
    
    if not active_url:
        print("\n❌ CRITICAL: Selected RAE Node is unreachable.")
        sys.exit(1)
    
    print(f"Connected to {active_url} ✅")
    log_session_start(active_url, session_id)
    fetch_black_box_context(active_url)
    print(f"\n✅ SESSION READY. All subsequent actions will be captured under {session_id}.")

if __name__ == "__main__":
    main()
