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
import shutil
from datetime import datetime
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
SESSIONS_DIR = COORDINATION_DIR / 'sessions'
ARCHIVE_DIR = COORDINATION_DIR / 'archive'
CONFIG_DIR = COORDINATION_DIR

class CoordinationWatcher(FileSystemEventHandler):
    """Watches coordination folder for changes and broadcasts updates."""

    def __init__(self):
        self.last_update = {}
        self.cooldown = 0.5  # Prevent rapid-fire updates
        print(f"👁️  CoordinationWatcher initialized")

    def on_any_event(self, event):
        """Debug: Log all events."""
        if not event.is_directory:
            print(f"📝 File event: {event.event_type} - {Path(event.src_path).name}")

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only care about JSON files
        if not event.src_path.endswith('.json'):
            print(f"⏭️  Skipping non-JSON file: {Path(event.src_path).name}")
            return

        # Cooldown to prevent duplicate events
        current_time = time.time()
        if event.src_path in self.last_update:
            if current_time - self.last_update[event.src_path] < self.cooldown:
                print(f"⏭️  Cooldown active for: {Path(event.src_path).name}")
                return

        self.last_update[event.src_path] = current_time

        # Broadcast update to all clients
        try:
            print(f"📡 Broadcasting update for: {Path(event.src_path).name}")
            data = load_coordination_data()
            broadcast_to_clients(data)
            print(f"✅ Broadcasted successfully (clients: {len(clients)})")
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
    session_ids = set()

    # Check coordination folder for current session
    orchestrator_file = COORDINATION_DIR / 'orchestrator_state.json'
    current_session_id = None
    if orchestrator_file.exists():
        try:
            with open(orchestrator_file, 'r') as f:
                state = json.load(f)
                current_session_id = state.get('session_id', 'current')
                sessions.append({
                    'session_id': current_session_id,
                    'start_time': state.get('start_time'),
                    'status': state.get('status', 'running'),
                    'is_current': True
                })
                session_ids.add(current_session_id)
        except Exception as e:
            print(f"⚠️  Error loading current session: {e}")

    # Check sessions history file
    history_file = COORDINATION_DIR / 'sessions_history.json'
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
                for session in history.get('sessions', []):
                    session_id = session.get('session_id')
                    if session_id and session_id not in session_ids:
                        sessions.append({
                            'session_id': session_id,
                            'start_time': session.get('start_time'),
                            'end_time': session.get('end_time'),
                            'status': session.get('status', 'completed'),
                            'is_current': False
                        })
                        session_ids.add(session_id)
        except Exception as e:
            print(f"⚠️  Error loading sessions history: {e}")

    # Check reports folder for historical sessions
    reports_dir = COORDINATION_DIR / 'reports'
    if reports_dir.exists():
        for report_file in reports_dir.glob('session_*.md'):
            session_id = report_file.stem.replace('session_', '')
            if session_id not in session_ids:
                # Try to extract timestamp from filename
                try:
                    # Parse bazinga_YYYYMMDD_HHMMSS format
                    import re
                    match = re.match(r'.*(\d{8})_(\d{6})', session_id)
                    if match:
                        date_str = match.group(1)
                        time_str = match.group(2)
                        from datetime import datetime
                        start_time = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S").isoformat()
                    else:
                        start_time = None
                except:
                    start_time = None

                sessions.append({
                    'session_id': session_id,
                    'start_time': start_time,
                    'status': 'completed',
                    'is_current': False
                })
                session_ids.add(session_id)

    # Sort sessions: current first, then by start time descending
    sessions.sort(key=lambda s: (not s.get('is_current', False), s.get('start_time', '') or ''), reverse=True)

    print(f"📊 Found {len(sessions)} sessions")
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
    config = load_dashboard_config()
    if not config.get('ai_diagrams_enabled', False):
        return jsonify({
            'error': 'AI diagram feature is disabled',
            'message': 'Enable in dashboard configuration'
        }), 403

    try:
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

# ===== New Enhanced Features =====

def load_dashboard_config():
    """Load dashboard configuration."""
    config_file = CONFIG_DIR / 'dashboard_config.json'
    default_config = {
        'ai_diagrams_enabled': False,
        'update_frequency': 5000,  # 5 seconds default
        'theme': 'dark',
        'notification_sound': True,
        'browser_notifications': True,
        'session_retention_days': 30,
        'email_notifications': {
            'enabled': False,
            'smtp_server': '',
            'smtp_port': 587,
            'from_email': '',
            'to_emails': []
        },
        'slack_notifications': {
            'enabled': False,
            'webhook_url': ''
        },
        'custom_triggers': []
    }

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except:
            pass

    return default_config

def save_dashboard_config(config):
    """Save dashboard configuration."""
    config_file = CONFIG_DIR / 'dashboard_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def save_session_snapshot(session_data):
    """Save a session snapshot for history."""
    SESSIONS_DIR.mkdir(exist_ok=True)

    session_id = session_data.get('session_id', f"session_{int(time.time())}")
    timestamp = datetime.now().isoformat()

    snapshot = {
        'session_id': session_id,
        'timestamp': timestamp,
        'data': session_data,
        'status': session_data.get('status', 'unknown')
    }

    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, 'w') as f:
        json.dump(snapshot, f, indent=2)

@app.route('/api/config', methods=['GET', 'POST'])
def dashboard_config():
    """Get or update dashboard configuration."""
    if request.method == 'GET':
        config = load_dashboard_config()
        return jsonify(config)
    else:
        try:
            new_config = request.json
            save_dashboard_config(new_config)
            return jsonify({'success': True, 'config': new_config})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/search', methods=['POST'])
def search_sessions():
    """Search sessions by content, date, status."""
    try:
        query = request.json.get('query', '')
        filters = request.json.get('filters', {})

        sessions = []

        # Load all session files
        if SESSIONS_DIR.exists():
            for session_file in SESSIONS_DIR.glob('*.json'):
                try:
                    with open(session_file, 'r') as f:
                        session = json.load(f)

                    # Apply filters
                    if filters.get('status') and session.get('status') != filters['status']:
                        continue

                    if filters.get('date_from'):
                        session_date = datetime.fromisoformat(session.get('timestamp', ''))
                        filter_date = datetime.fromisoformat(filters['date_from'])
                        if session_date < filter_date:
                            continue

                    if filters.get('date_to'):
                        session_date = datetime.fromisoformat(session.get('timestamp', ''))
                        filter_date = datetime.fromisoformat(filters['date_to'])
                        if session_date > filter_date:
                            continue

                    # Search in content
                    if query:
                        session_str = json.dumps(session).lower()
                        if query.lower() not in session_str:
                            continue

                    sessions.append(session)
                except:
                    continue

        # Sort by timestamp, newest first
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify({'sessions': sessions, 'count': len(sessions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET', 'DELETE'])
def manage_session(session_id):
    """Get or delete a specific session."""
    session_file = SESSIONS_DIR / f"{session_id}.json"

    if request.method == 'GET':
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404

        try:
            with open(session_file, 'r') as f:
                session = json.load(f)
            return jsonify(session)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404

        try:
            session_file.unlink()
            return jsonify({'success': True, 'message': 'Session deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/archive', methods=['POST'])
def archive_session(session_id):
    """Archive a session."""
    session_file = SESSIONS_DIR / f"{session_id}.json"

    if not session_file.exists():
        return jsonify({'error': 'Session not found'}), 404

    try:
        ARCHIVE_DIR.mkdir(exist_ok=True)
        archive_file = ARCHIVE_DIR / f"{session_id}.json"
        shutil.move(str(session_file), str(archive_file))
        return jsonify({'success': True, 'message': 'Session archived'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session data."""
    session_file = SESSIONS_DIR / f"{session_id}.json"

    if not session_file.exists():
        return jsonify({'error': 'Session not found'}), 404

    try:
        with open(session_file, 'r') as f:
            session = json.load(f)

        export_format = request.args.get('format', 'json')

        if export_format == 'json':
            return jsonify(session)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/compare', methods=['POST'])
def compare_sessions():
    """Compare two sessions."""
    try:
        session1_id = request.json.get('session1')
        session2_id = request.json.get('session2')

        session1_file = SESSIONS_DIR / f"{session1_id}.json"
        session2_file = SESSIONS_DIR / f"{session2_id}.json"

        if not session1_file.exists() or not session2_file.exists():
            return jsonify({'error': 'One or both sessions not found'}), 404

        with open(session1_file, 'r') as f:
            session1 = json.load(f)
        with open(session2_file, 'r') as f:
            session2 = json.load(f)

        # Generate comparison
        comparison = {
            'session1': session1,
            'session2': session2,
            'differences': generate_session_diff(session1, session2)
        }

        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_session_diff(session1, session2):
    """Generate differences between two sessions."""
    diffs = []

    # Compare key metrics
    s1_data = session1.get('data', {})
    s2_data = session2.get('data', {})

    # Compare statuses
    if s1_data.get('status') != s2_data.get('status'):
        diffs.append({
            'field': 'status',
            'session1': s1_data.get('status'),
            'session2': s2_data.get('status')
        })

    # Compare task groups if present
    s1_groups = s1_data.get('group_status', {}).get('task_groups', [])
    s2_groups = s2_data.get('group_status', {}).get('task_groups', [])

    if len(s1_groups) != len(s2_groups):
        diffs.append({
            'field': 'task_group_count',
            'session1': len(s1_groups),
            'session2': len(s2_groups)
        })

    return diffs

@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    """Get timeline data for agent execution visualization."""
    try:
        data = load_coordination_data()
        log = load_orchestration_log()
        timeline = []

        # Parse orchestrator state for session start
        orch_state = data.get('orchestrator_state', {})
        if orch_state and orch_state.get('start_time'):
            timeline.append({
                'agent': 'Orchestrator',
                'action': 'Started Session',
                'timestamp': orch_state.get('start_time'),
                'duration': 0,
                'status': 'completed'
            })

        # Parse orchestration log for agent activities
        if log and log.get('entries'):
            for entry in log.get('entries', []):
                header = entry.get('header', '')

                # Parse header: ## [TIMESTAMP] Iteration N - Agent Type (Group X)
                import re
                match = re.match(r'##\s*\[([^\]]+)\]\s*Iteration\s*(\d+)\s*-\s*([^(]+)(?:\(Group\s*([^\)]+)\))?', header)

                if match:
                    timestamp_str, iteration, agent_type, group_id = match.groups()
                    agent_type = agent_type.strip()

                    # Map agent types to display names
                    agent_map = {
                        'Project Manager': 'PM',
                        'Developer': 'Developer',
                        'QA Expert': 'QA',
                        'Tech Lead': 'Tech Lead'
                    }

                    display_agent = agent_map.get(agent_type, agent_type)
                    action = f"Iteration {iteration}"
                    if group_id:
                        action += f" (Group {group_id.strip()})"

                    timeline.append({
                        'agent': display_agent,
                        'action': action,
                        'timestamp': timestamp_str,
                        'duration': 60,  # Estimate 60 seconds per agent action
                        'status': 'completed'
                    })

        # If no log entries, try to build from PM state
        if not timeline or len(timeline) == 1:
            pm_state = data.get('pm_state', {})
            if pm_state and pm_state.get('task_groups'):
                # Add estimated entries based on groups
                groups = pm_state.get('task_groups', {})
                for group_id, group in groups.items():
                    status = group.get('status', 'pending')
                    if status != 'pending':
                        # Add developer entry
                        timeline.append({
                            'agent': 'Developer',
                            'action': f"Implemented {group.get('name', group_id)}",
                            'timestamp': orch_state.get('start_time'),
                            'duration': 120,
                            'status': 'completed' if status == 'completed' else 'in-progress'
                        })

                        # Add QA if applicable
                        if status in ['completed', 'in_qa', 'in_review']:
                            timeline.append({
                                'agent': 'QA',
                                'action': f"Tested {group.get('name', group_id)}",
                                'timestamp': orch_state.get('start_time'),
                                'duration': 90,
                                'status': 'completed'
                            })

                        # Add Tech Lead if completed
                        if status == 'completed':
                            timeline.append({
                                'agent': 'Tech Lead',
                                'action': f"Reviewed {group.get('name', group_id)}",
                                'timestamp': orch_state.get('start_time'),
                                'duration': 60,
                                'status': 'completed'
                            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x.get('timestamp', '') or '')

        return jsonify({'timeline': timeline})
    except Exception as e:
        print(f"⚠️  Error generating timeline: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'timeline': []}), 500

@app.route('/api/logs/stream', methods=['GET'])
def stream_logs():
    """Stream real-time logs."""
    try:
        print(f"📋 /api/logs/stream requested")
        log_file = DOCS_DIR / 'orchestration-log.md'

        if not log_file.exists():
            print(f"⚠️  Log file not found: {log_file}")
            return jsonify({'logs': [], 'total': 0, 'message': 'No log file found'})

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get last N lines
        lines = content.split('\n')
        limit = int(request.args.get('limit', 100))
        recent_lines = lines[-limit:] if len(lines) > limit else lines

        print(f"✅ Returning {len(recent_lines)} log lines (total: {len(lines)})")
        return jsonify({'logs': recent_lines, 'total': len(lines)})

    except ValueError as e:
        print(f"⚠️  Invalid limit parameter: {e}")
        return jsonify({'error': 'Invalid limit parameter', 'logs': []}), 400
    except Exception as e:
        print(f"❌ Error streaming logs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'logs': []}), 500

@sock.route('/ws')
def websocket(ws):
    """WebSocket endpoint for real-time updates."""
    clients.append(ws)
    print(f"✅ Client connected (total: {len(clients)})")
    print(f"   Client info: {ws}")

    try:
        # Send initial data
        print(f"📤 Sending initial data to client...")
        data = load_coordination_data()
        ws.send(json.dumps(data))
        print(f"✅ Initial data sent successfully")

        # Keep connection alive
        while True:
            message = ws.receive()
            if message:
                print(f"💓 Heartbeat received from client")
                # Echo back for heartbeat
                ws.send(json.dumps({'type': 'pong'}))
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
        import traceback
        traceback.print_exc()
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

    print(f"\n{'='*60}")
    print(f"🔍 Setting up file watcher...")
    print(f"{'='*60}")
    print(f"📁 Watching directory: {COORDINATION_DIR.absolute()}")

    # List current JSON files
    json_files = list(COORDINATION_DIR.glob('*.json'))
    print(f"📋 Current JSON files ({len(json_files)}):")
    for f in json_files:
        print(f"   - {f.name}")

    if not json_files:
        print(f"⚠️  No JSON files found yet - waiting for orchestration to start...")

    event_handler = CoordinationWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(COORDINATION_DIR), recursive=False)
    observer.start()
    print(f"✅ File watcher started successfully")
    print(f"{'='*60}\n")
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
