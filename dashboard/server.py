#!/usr/bin/env python3
"""
BAZINGA Dashboard Server
========================
Lightweight WebSocket server for real-time orchestration monitoring.
Queries database for real-time state and logs.
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

# Import BazingaDB for database operations
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / 'bazinga-db' / 'scripts'))
from bazinga_db import BazingaDB

app = Flask(__name__, static_folder='.')
sock = Sock(app)

# Store connected WebSocket clients
clients = []

# Base paths
BASE_DIR = Path(__file__).parent.parent
BAZINGA_DIR = BASE_DIR / 'bazinga'
DOCS_DIR = BASE_DIR / 'docs'
ARCHIVE_DIR = BAZINGA_DIR / 'archive'
CONFIG_DIR = BAZINGA_DIR
DB_PATH = BAZINGA_DIR / 'bazinga.db'

# Initialize database connection
db = None

class CoordinationWatcher(FileSystemEventHandler):
    """Watches database file for changes and broadcasts updates."""

    def __init__(self):
        self.last_update = {}
        self.cooldown = 0.5  # Prevent rapid-fire updates
        print(f"👁️  CoordinationWatcher initialized (database mode)")

    def on_any_event(self, event):
        """Debug: Log all events."""
        if not event.is_directory:
            print(f"📝 File event: {event.event_type} - {Path(event.src_path).name}")

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only care about database file changes (including WAL files)
        filename = Path(event.src_path).name
        if not (filename == 'bazinga.db' or filename.startswith('bazinga.db-')):
            print(f"⏭️  Skipping non-database file: {filename}")
            return

        # Cooldown to prevent duplicate events
        current_time = time.time()
        if event.src_path in self.last_update:
            if current_time - self.last_update[event.src_path] < self.cooldown:
                print(f"⏭️  Cooldown active for: {filename}")
                return

        self.last_update[event.src_path] = current_time

        # Broadcast update to all clients
        try:
            print(f"📡 Broadcasting database update")
            data = load_bazinga_data()
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

def get_current_session_id():
    """Get the most recent active session ID from database."""
    global db
    if not db or not DB_PATH.exists():
        return None

    try:
        # Query for most recent active session
        sessions = db.query("""
            SELECT session_id FROM sessions
            WHERE status = 'active'
            ORDER BY start_time DESC
            LIMIT 1
        """)

        if sessions:
            return sessions[0]['session_id']

        # If no active sessions, get most recent session
        sessions = db.query("""
            SELECT session_id FROM sessions
            ORDER BY start_time DESC
            LIMIT 1
        """)

        return sessions[0]['session_id'] if sessions else None
    except Exception as e:
        print(f"⚠️  Error getting current session: {e}")
        return None

def load_bazinga_data():
    """Load all coordination state from database."""
    global db

    data = {
        'timestamp': time.time(),
        'orchestrator_state': None,
        'pm_state': None,
        'group_status': None,
        'quality_dashboard': None,
        'skills_config': None
    }

    if not db or not DB_PATH.exists():
        print(f"⚠️  Database not available at {DB_PATH}")
        return data

    try:
        # Get current session ID
        session_id = get_current_session_id()
        if not session_id:
            print(f"⚠️  No active session found")
            return data

        # Get dashboard snapshot (efficient single query)
        snapshot = db.get_dashboard_snapshot(session_id)

        # Map database data to expected format
        data['orchestrator_state'] = snapshot.get('orchestrator_state')
        data['pm_state'] = snapshot.get('pm_state')

        # Convert task_groups array to group_status object
        task_groups = snapshot.get('task_groups', [])
        if task_groups:
            data['group_status'] = {
                'task_groups': {
                    group['id']: {
                        'name': group['name'],
                        'status': group['status'],
                        'assigned_to': group.get('assigned_to'),
                        'revision_count': group.get('revision_count', 0),
                        'last_review_status': group.get('last_review_status')
                    }
                    for group in task_groups
                }
            }

        # Load skills config from database configuration table
        data['skills_config'] = db.get_config('skills_config')

        # Load quality dashboard config if exists
        data['quality_dashboard'] = db.get_config('quality_dashboard')

        print(f"✅ Loaded data for session: {session_id}")

    except Exception as e:
        print(f"⚠️  Error loading coordination data from database: {e}")
        import traceback
        traceback.print_exc()

    return data

def load_orchestration_log():
    """Load and parse orchestration log from database."""
    global db

    if not db or not DB_PATH.exists():
        print(f"⚠️  Database not available")
        return {'content': '', 'entries': []}

    try:
        # Get current session ID
        session_id = get_current_session_id()
        if not session_id:
            print(f"⚠️  No active session found")
            return {'content': '', 'entries': []}

        # Get logs from database in markdown format
        content = db.stream_logs(session_id, limit=1000)

        # Parse log entries from markdown
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
        print(f"⚠️  Error loading orchestration log from database: {e}")
        import traceback
        traceback.print_exc()
        return {'content': '', 'entries': []}

def list_sessions():
    """List all available orchestration sessions from database."""
    global db

    if not db or not DB_PATH.exists():
        print(f"⚠️  Database not available")
        return []

    try:
        # Query all sessions from database
        all_sessions = db.query("""
            SELECT session_id, start_time, end_time, mode, status, original_requirements
            FROM sessions
            ORDER BY start_time DESC
        """)

        sessions = []
        for row in all_sessions:
            sessions.append({
                'session_id': row['session_id'],
                'start_time': row['start_time'],
                'end_time': row.get('end_time'),
                'mode': row.get('mode'),
                'status': row['status'],
                'original_requirements': row.get('original_requirements'),
                'is_current': row['status'] == 'active'
            })

        print(f"📊 Found {len(sessions)} sessions in database")
        return sessions

    except Exception as e:
        print(f"⚠️  Error loading sessions from database: {e}")
        import traceback
        traceback.print_exc()
        return []

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
    data = load_bazinga_data()
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
        data = load_bazinga_data()

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
    global db

    if not db or not DB_PATH.exists():
        return jsonify({'error': 'Database not available'}), 500

    try:
        query = request.json.get('query', '')
        filters = request.json.get('filters', {})

        # Build SQL query with filters
        sql = "SELECT * FROM sessions WHERE 1=1"
        params = []

        # Apply status filter
        if filters.get('status'):
            sql += " AND status = ?"
            params.append(filters['status'])

        # Apply date range filters
        if filters.get('date_from'):
            sql += " AND created_at >= ?"
            params.append(filters['date_from'])

        if filters.get('date_to'):
            sql += " AND created_at <= ?"
            params.append(filters['date_to'])

        # Execute query
        all_sessions = db.query(sql, params)

        # Apply text search if query provided
        sessions = []
        for session_data in all_sessions:
            if query:
                # Search in original requirements and session metadata
                searchable = json.dumps({
                    'session_id': session_data.get('session_id'),
                    'requirements': session_data.get('original_requirements'),
                    'mode': session_data.get('mode'),
                    'status': session_data.get('status')
                }).lower()

                if query.lower() not in searchable:
                    continue

            # Format session for frontend
            sessions.append({
                'session_id': session_data.get('session_id'),
                'status': session_data.get('status'),
                'mode': session_data.get('mode'),
                'timestamp': session_data.get('created_at'),
                'created_at': session_data.get('created_at'),
                'end_time': session_data.get('end_time'),
                'original_requirements': session_data.get('original_requirements')
            })

        # Sort by timestamp, newest first
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify({'sessions': sessions, 'count': len(sessions)})
    except Exception as e:
        print(f"⚠️  Error searching sessions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET', 'DELETE'])
def manage_session(session_id):
    """Get or delete a specific session."""
    global db

    if request.method == 'GET':
        if not db or not DB_PATH.exists():
            return jsonify({'error': 'Database not available'}), 500

        try:
            # Get session data from database
            session_data = db.get_session(session_id)
            if not session_data:
                return jsonify({'error': 'Session not found'}), 404

            # Get full snapshot with all related data
            snapshot = db.get_dashboard_snapshot(session_id)

            # Build response in expected format
            response = {
                'session_id': session_id,
                'mode': session_data.get('mode'),
                'status': session_data.get('status'),
                'created_at': session_data.get('created_at'),
                'end_time': session_data.get('end_time'),
                'original_requirements': session_data.get('original_requirements'),
                'orchestrator_state': snapshot.get('orchestrator_state'),
                'pm_state': snapshot.get('pm_state'),
                'task_groups': snapshot.get('task_groups', []),
                'logs': snapshot.get('recent_logs', []),
                'token_usage': snapshot.get('token_usage')
            }

            return jsonify(response)
        except Exception as e:
            print(f"⚠️  Error getting session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        if not db or not DB_PATH.exists():
            return jsonify({'error': 'Database not available'}), 500

        try:
            # Delete session from database
            session_data = db.get_session(session_id)
            if not session_data:
                return jsonify({'error': 'Session not found'}), 404

            # Update session status to 'deleted' instead of hard delete
            db.update_session_status(session_id, 'deleted')
            return jsonify({'success': True, 'message': 'Session deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/archive', methods=['POST'])
def archive_session(session_id):
    """Archive a session (mark as archived in database)."""
    global db

    if not db or not DB_PATH.exists():
        return jsonify({'error': 'Database not available'}), 500

    try:
        # Check if session exists
        session_data = db.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404

        # Update session status to 'archived'
        db.update_session_status(session_id, 'archived')

        return jsonify({'success': True, 'message': 'Session archived'})
    except Exception as e:
        print(f"⚠️  Error archiving session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session data from database."""
    global db

    if not db or not DB_PATH.exists():
        return jsonify({'error': 'Database not available'}), 500

    try:
        # Get session data from database
        session_data = db.get_session(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404

        # Get full snapshot with all related data
        snapshot = db.get_dashboard_snapshot(session_id)

        # Build complete export
        export_data = {
            'session': session_data,
            'orchestrator_state': snapshot.get('orchestrator_state'),
            'pm_state': snapshot.get('pm_state'),
            'task_groups': snapshot.get('task_groups', []),
            'logs': snapshot.get('recent_logs', []),
            'token_usage': snapshot.get('token_usage'),
            'exported_at': datetime.now().isoformat()
        }

        export_format = request.args.get('format', 'json')

        if export_format == 'json':
            return jsonify(export_data)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        print(f"⚠️  Error exporting session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/compare', methods=['POST'])
def compare_sessions():
    """Compare two sessions from database."""
    global db

    if not db or not DB_PATH.exists():
        return jsonify({'error': 'Database not available'}), 500

    try:
        session1_id = request.json.get('session1')
        session2_id = request.json.get('session2')

        # Get both sessions from database
        session1_data = db.get_session(session1_id)
        session2_data = db.get_session(session2_id)

        if not session1_data or not session2_data:
            return jsonify({'error': 'One or both sessions not found'}), 404

        # Get snapshots for both sessions
        snapshot1 = db.get_dashboard_snapshot(session1_id)
        snapshot2 = db.get_dashboard_snapshot(session2_id)

        # Build session objects for comparison
        session1 = {
            'session_id': session1_id,
            'data': {
                'status': session1_data.get('status'),
                'mode': session1_data.get('mode'),
                'created_at': session1_data.get('created_at'),
                'end_time': session1_data.get('end_time'),
                'group_status': {'task_groups': snapshot1.get('task_groups', [])},
                'pm_state': snapshot1.get('pm_state'),
                'token_usage': snapshot1.get('token_usage')
            }
        }

        session2 = {
            'session_id': session2_id,
            'data': {
                'status': session2_data.get('status'),
                'mode': session2_data.get('mode'),
                'created_at': session2_data.get('created_at'),
                'end_time': session2_data.get('end_time'),
                'group_status': {'task_groups': snapshot2.get('task_groups', [])},
                'pm_state': snapshot2.get('pm_state'),
                'token_usage': snapshot2.get('token_usage')
            }
        }

        # Generate comparison
        comparison = {
            'session1': session1,
            'session2': session2,
            'differences': generate_session_diff(session1, session2)
        }

        return jsonify(comparison)
    except Exception as e:
        print(f"⚠️  Error comparing sessions: {e}")
        import traceback
        traceback.print_exc()
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
        data = load_bazinga_data()
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
    """Stream real-time logs from database."""
    global db

    try:
        print(f"📋 /api/logs/stream requested")

        if not db or not DB_PATH.exists():
            print(f"⚠️  Database not available")
            return jsonify({'logs': [], 'total': 0, 'message': 'Database not available'})

        # Get current session ID
        session_id = get_current_session_id()
        if not session_id:
            print(f"⚠️  No active session found")
            return jsonify({'logs': [], 'total': 0, 'message': 'No active session'})

        # Get limit parameter
        limit = int(request.args.get('limit', 100))

        # Get logs from database
        logs = db.get_logs(session_id, limit=limit)

        # Format logs as lines
        log_lines = []
        for log in reversed(logs):  # Show oldest first
            timestamp = log['timestamp']
            agent_type = log['agent_type'].upper() if log['agent_type'] else 'UNKNOWN'
            iteration = log['iteration'] if log['iteration'] else '?'
            content = log['content']

            # Format as markdown-like structure
            log_lines.append(f"## [{timestamp}] Iteration {iteration} - {agent_type}")
            log_lines.append("")
            log_lines.append(content)
            log_lines.append("")
            log_lines.append("---")
            log_lines.append("")

        total_count = len(logs)
        print(f"✅ Returning {len(log_lines)} log lines from {total_count} entries")
        return jsonify({'logs': log_lines, 'total': total_count})

    except ValueError as e:
        print(f"⚠️  Invalid limit parameter: {e}")
        return jsonify({'error': 'Invalid limit parameter', 'logs': []}), 400
    except Exception as e:
        print(f"❌ Error streaming logs from database: {e}")
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
        data = load_bazinga_data()
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
    """Start watching database file for changes."""
    if not BAZINGA_DIR.exists():
        print(f"⚠️  Coordination folder not found: {BAZINGA_DIR}")
        print("   Dashboard will start, but won't receive updates.")
        return

    print(f"\n{'='*60}")
    print(f"🔍 Setting up database watcher...")
    print(f"{'='*60}")
    print(f"📁 Watching directory: {BAZINGA_DIR.absolute()}")
    print(f"📊 Database file: {DB_PATH.name}")

    if DB_PATH.exists():
        print(f"✅ Database file exists ({DB_PATH.stat().st_size} bytes)")
    else:
        print(f"⚠️  Database not found yet - waiting for initialization...")

    event_handler = CoordinationWatcher()
    observer = Observer()
    observer.schedule(event_handler, str(BAZINGA_DIR), recursive=False)
    observer.start()
    print(f"✅ Database watcher started successfully")
    print(f"{'='*60}\n")
    return observer

def main():
    """Start dashboard server."""
    global db

    port = int(os.environ.get('DASHBOARD_PORT', 53124))

    print("=" * 60)
    print("🚀 BAZINGA Orchestration Dashboard")
    print("=" * 60)
    print(f"📡 Server: http://localhost:{port}")
    print(f"🌐 Dashboard: http://localhost:{port}/")
    print(f"📁 Coordination: {BAZINGA_DIR}")
    print(f"🗄️  Database: {DB_PATH}")
    print("=" * 60)

    # Initialize database connection
    if DB_PATH.exists():
        try:
            db = BazingaDB(str(DB_PATH))
            print(f"✅ Database connection established")
        except Exception as e:
            print(f"⚠️  Failed to connect to database: {e}")
            print("   Dashboard will start in limited mode")
    else:
        print(f"⚠️  Database not found - dashboard will wait for initialization")

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
