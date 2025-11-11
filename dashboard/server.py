#!/usr/bin/env python3
"""
BAZINGA Dashboard Server
========================
Lightweight WebSocket server for real-time orchestration monitoring.
Watches coordination folder and pushes updates to connected clients.
"""

import json
import os
import sys
import time
from pathlib import Path
from threading import Thread
from flask import Flask, send_from_directory, jsonify, request
from flask_sock import Sock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__, static_folder='.')
sock = Sock(app)

# Store connected WebSocket clients
clients = []

# Base paths
BASE_DIR = Path(__file__).parent.parent
COORDINATION_DIR = BASE_DIR / 'coordination'
DOCS_DIR = BASE_DIR / 'docs'

class CoordinationWatcher(FileSystemEventHandler):
    """Watches coordination folder for changes and broadcasts updates."""

    def __init__(self):
        self.last_update = {}
        self.cooldown = 0.5  # Prevent rapid-fire updates

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only care about JSON files
        if not event.src_path.endswith('.json'):
            return

        # Cooldown to prevent duplicate events
        current_time = time.time()
        if event.src_path in self.last_update:
            if current_time - self.last_update[event.src_path] < self.cooldown:
                return

        self.last_update[event.src_path] = current_time

        # Broadcast update to all clients
        try:
            data = load_coordination_data()
            broadcast_to_clients(data)
            print(f"📡 Broadcasted update: {Path(event.src_path).name}")
        except Exception as e:
            print(f"⚠️  Error broadcasting update: {e}")

def broadcast_to_clients(data):
    """Send data to all connected WebSocket clients."""
    disconnected = []
    for client in clients:
        try:
            client.send(json.dumps(data))
        except Exception as e:
            print(f"⚠️  Client disconnected: {e}")
            disconnected.append(client)

    # Clean up disconnected clients
    for client in disconnected:
        if client in clients:
            clients.remove(client)

def load_coordination_data():
    """Load all coordination state files."""
    data = {
        'timestamp': time.time(),
        'orchestrator_state': None,
        'pm_state': None,
        'group_status': None,
        'quality_dashboard': None,
        'skills_config': None
    }

    # Load orchestrator state
    orchestrator_file = COORDINATION_DIR / 'orchestrator_state.json'
    if orchestrator_file.exists():
        try:
            with open(orchestrator_file, 'r') as f:
                data['orchestrator_state'] = json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading orchestrator_state.json: {e}")

    # Load PM state
    pm_file = COORDINATION_DIR / 'pm_state.json'
    if pm_file.exists():
        try:
            with open(pm_file, 'r') as f:
                data['pm_state'] = json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading pm_state.json: {e}")

    # Load group status
    group_file = COORDINATION_DIR / 'group_status.json'
    if group_file.exists():
        try:
            with open(group_file, 'r') as f:
                data['group_status'] = json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading group_status.json: {e}")

    # Load quality dashboard
    quality_file = COORDINATION_DIR / 'quality_dashboard.json'
    if quality_file.exists():
        try:
            with open(quality_file, 'r') as f:
                data['quality_dashboard'] = json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading quality_dashboard.json: {e}")

    # Load skills config
    skills_file = COORDINATION_DIR / 'skills_config.json'
    if skills_file.exists():
        try:
            with open(skills_file, 'r') as f:
                data['skills_config'] = json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading skills_config.json: {e}")

    return data

def load_orchestration_log():
    """Load and parse orchestration log."""
    log_file = DOCS_DIR / 'orchestration-log.md'
    if not log_file.exists():
        return {'content': '', 'entries': []}

    try:
        with open(log_file, 'r') as f:
            content = f.read()

        # Parse log entries (basic parsing)
        entries = []
        current_entry = None

        for line in content.split('\n'):
            # Detect iteration headers
            if line.startswith('## [') and 'Iteration' in line:
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    'header': line,
                    'content': []
                }
            elif current_entry:
                current_entry['content'].append(line)

        if current_entry:
            entries.append(current_entry)

        return {
            'content': content,
            'entries': entries,
            'count': len(entries)
        }
    except Exception as e:
        print(f"⚠️  Error loading orchestration log: {e}")
        return {'content': '', 'entries': []}

def list_sessions():
    """List all available orchestration sessions."""
    sessions = []

    # Check coordination folder for current session
    orchestrator_file = COORDINATION_DIR / 'orchestrator_state.json'
    if orchestrator_file.exists():
        try:
            with open(orchestrator_file, 'r') as f:
                state = json.load(f)
                sessions.append({
                    'session_id': state.get('session_id', 'current'),
                    'start_time': state.get('start_time'),
                    'status': state.get('status', 'unknown'),
                    'is_current': True
                })
        except:
            pass

    # Check reports folder for historical sessions
    reports_dir = COORDINATION_DIR / 'reports'
    if reports_dir.exists():
        for report_file in reports_dir.glob('session_*.md'):
            session_id = report_file.stem.replace('session_', '')
            sessions.append({
                'session_id': session_id,
                'start_time': session_id,  # Parse from filename if needed
                'status': 'completed',
                'is_current': False
            })

    return sessions

# Routes

@app.route('/')
def index():
    """Serve main dashboard page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, assets)."""
    return send_from_directory('.', path)

@app.route('/api/data')
def get_data():
    """Get all coordination data."""
    data = load_coordination_data()
    return jsonify(data)

@app.route('/api/log')
def get_log():
    """Get orchestration log."""
    log_data = load_orchestration_log()
    return jsonify(log_data)

@app.route('/api/sessions')
def get_sessions():
    """Get list of all sessions."""
    sessions = list_sessions()
    return jsonify(sessions)

@app.route('/api/ai-diagram', methods=['POST'])
def generate_ai_diagram():
    """Generate AI-powered workflow diagram (if enabled)."""
    # Check if feature is enabled
    skills_file = COORDINATION_DIR / 'skills_config.json'
    if not skills_file.exists():
        return jsonify({'error': 'Skills config not found'}), 404

    try:
        with open(skills_file, 'r') as f:
            skills_config = json.load(f)

        if not skills_config.get('dashboard_ai_diagram_enabled', False):
            return jsonify({
                'error': 'AI diagram feature is disabled',
                'message': 'Enable in coordination/skills_config.json by setting dashboard_ai_diagram_enabled: true'
            }), 403

        # Get current state
        data = load_coordination_data()

        # Get API key from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY not set'}), 500

        # Import anthropic client
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Build prompt
        prompt = f"""You are visualizing a BAZINGA orchestration workflow.

Current state:
{json.dumps(data, indent=2)}

Please generate:
1. A Mermaid diagram showing the workflow graph with:
   - Task groups as nodes
   - Dependencies as edges
   - Color-coded by status (green=completed, orange=in-progress, gray=pending)
   - Agent progression indicators (dev → QA → TL)
2. A brief narrative explaining the current workflow state
3. Key insights about the orchestration progress

Return ONLY a JSON object with this structure:
{{
    "mermaid": "graph TD\\n...",
    "narrative": "The workflow is currently...",
    "insights": ["Insight 1", "Insight 2"]
}}

Make the Mermaid diagram visually clear and informative."""

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        response_text = message.content[0].text

        # Try to extract JSON from response
        try:
            # Find JSON in response (might be wrapped in markdown code blocks)
            if '```json' in response_text:
                json_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_text = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_text = response_text

            result = json.loads(json_text)
            return jsonify(result)
        except:
            # If parsing fails, return raw response
            return jsonify({
                'mermaid': '',
                'narrative': response_text,
                'insights': []
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sock.route('/ws')
def websocket(ws):
    """WebSocket endpoint for real-time updates."""
    clients.append(ws)
    print(f"✅ Client connected (total: {len(clients)})")

    try:
        # Send initial data
        data = load_coordination_data()
        ws.send(json.dumps(data))

        # Keep connection alive
        while True:
            message = ws.receive()
            if message:
                # Echo back for heartbeat
                ws.send(json.dumps({'type': 'pong'}))
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
    finally:
        if ws in clients:
            clients.remove(ws)
        print(f"❌ Client disconnected (remaining: {len(clients)})")

def start_file_watcher():
    """Start watching coordination folder for changes."""
    if not COORDINATION_DIR.exists():
        print(f"⚠️  Coordination folder not found: {COORDINATION_DIR}")
        print("   Dashboard will start, but won't receive updates until orchestration begins.")
        return

    event_handler = CoordinationWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(COORDINATION_DIR), recursive=False)
    observer.start()
    print(f"👁️  Watching: {COORDINATION_DIR}")
    return observer

def main():
    """Start dashboard server."""
    port = int(os.environ.get('DASHBOARD_PORT', 53124))

    print("=" * 60)
    print("🚀 BAZINGA Orchestration Dashboard")
    print("=" * 60)
    print(f"📡 Server: http://localhost:{port}")
    print(f"🌐 Dashboard: http://localhost:{port}/")
    print(f"📁 Coordination: {COORDINATION_DIR}")
    print("=" * 60)

    # Start file watcher in background thread
    observer = start_file_watcher()

    try:
        # Start Flask app
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down dashboard...")
        if observer:
            observer.stop()
            observer.join()
        print("✅ Dashboard stopped")
        sys.exit(0)

if __name__ == '__main__':
    main()
