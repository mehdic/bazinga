#!/usr/bin/env python3
"""Mini Session Dashboard - Minimal Flask server for BAZINGA monitoring.

A lightweight alternative to dashboard-v2 for real-time orchestration monitoring.
Run with: python server.py
Opens at: http://localhost:5050
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request

# Determine the base path - handle both dev mode and installed mode
SCRIPT_DIR = Path(__file__).parent.resolve()
if SCRIPT_DIR.name == 'mini-dashboard':
    # Could be dev mode (mini-dashboard at repo root) or installed (bazinga/mini-dashboard)
    if SCRIPT_DIR.parent.name == 'bazinga':
        # Installed mode: bazinga/mini-dashboard -> bazinga/bazinga.db
        DEFAULT_DB = SCRIPT_DIR.parent / 'bazinga.db'
    else:
        # Dev mode: mini-dashboard at repo root -> bazinga/bazinga.db
        DEFAULT_DB = SCRIPT_DIR.parent / 'bazinga' / 'bazinga.db'
else:
    DEFAULT_DB = Path('bazinga/bazinga.db')

DB_PATH = os.environ.get('BAZINGA_DB_PATH', str(DEFAULT_DB))

# Disable static file serving from current directory (security)
app = Flask(__name__, static_folder=None)


def get_db():
    """Get read-only database connection with busy timeout."""
    db_file = Path(DB_PATH)
    if not db_file.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=2000")
    return conn


def parse_status(content: str) -> str:
    """Extract status from agent response content."""
    if not content:
        return 'UNKNOWN'

    # Try to find JSON objects with status field
    try:
        # Look for JSON blocks in content (last one is usually the summary)
        json_matches = re.findall(r'\{[^{}]+\}', content)
        for match in reversed(json_matches):
            try:
                data = json.loads(match)
                if 'status' in data:
                    return str(data['status']).upper()
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    # Fallback: regex for common status patterns
    patterns = [
        r'"status"\s*:\s*"([A-Z_]+)"',  # JSON format
        r'status:\s*([A-Z_]+)',          # YAML-like format
        r'\*\*Status\*\*:\s*([A-Z_]+)',  # Markdown format
        r'Status:\s*([A-Z_]+)',          # Plain format
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    # Check for common status keywords in content
    status_keywords = {
        'READY_FOR_QA': ['ready for qa', 'ready_for_qa'],
        'PASS': ['tests pass', 'all tests pass', 'pass'],
        'FAIL': ['tests fail', 'failure', 'failed'],
        'APPROVED': ['approved', 'lgtm'],
        'CHANGES_REQUESTED': ['changes requested', 'needs changes'],
        'BAZINGA': ['bazinga'],
        'IN_PROGRESS': ['in progress', 'working on'],
    }

    content_lower = content.lower()
    for status, keywords in status_keywords.items():
        for keyword in keywords:
            if keyword in content_lower:
                return status

    return 'ACTIVE'  # Default for agents that are working


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(str(SCRIPT_DIR), 'index.html')


@app.route('/api/health')
def health():
    """Health check endpoint."""
    conn = None
    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "db_path": DB_PATH})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/sessions')
def get_sessions():
    """Get recent sessions (active first)."""
    conn = None
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT session_id, status, mode, original_requirements,
                   start_time, end_time, created_at
            FROM sessions
            ORDER BY
                CASE status WHEN 'active' THEN 0 ELSE 1 END,
                COALESCE(created_at, start_time) DESC
            LIMIT 10
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    except FileNotFoundError as e:
        return jsonify({"error": str(e), "sessions": []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/agents')
def get_agents(session_id):
    """Get spawned agents with parsed status, ordered by first appearance."""
    conn = None
    try:
        conn = get_db()

        # Get unique agents with their latest log entry and stats
        rows = conn.execute("""
            SELECT
                l.agent_type,
                l.agent_id,
                l.content,
                l.timestamp as last_activity,
                (SELECT MIN(timestamp) FROM orchestration_logs l2
                 WHERE l2.session_id = l.session_id
                   AND l2.agent_type = l.agent_type
                   AND COALESCE(l2.agent_id, '') = COALESCE(l.agent_id, '')) as first_seen,
                (SELECT COUNT(*) FROM orchestration_logs l2
                 WHERE l2.session_id = l.session_id
                   AND l2.agent_type = l.agent_type
                   AND COALESCE(l2.agent_id, '') = COALESCE(l.agent_id, '')
                   AND l2.log_type = 'reasoning') as reasoning_count,
                (SELECT COUNT(*) FROM orchestration_logs l2
                 WHERE l2.session_id = l.session_id
                   AND l2.agent_type = l.agent_type
                   AND COALESCE(l2.agent_id, '') = COALESCE(l.agent_id, '')) as total_logs,
                (SELECT SUM(tokens_estimated) FROM token_usage t
                 WHERE t.session_id = l.session_id
                   AND t.agent_type = l.agent_type) as tokens
            FROM orchestration_logs l
            WHERE l.session_id = ?
              AND l.id = (
                  SELECT MAX(id) FROM orchestration_logs l2
                  WHERE l2.session_id = l.session_id
                    AND l2.agent_type = l.agent_type
                    AND COALESCE(l2.agent_id, '') = COALESCE(l.agent_id, ''))
            ORDER BY first_seen ASC
        """, (session_id,)).fetchall()

        agents = []
        for r in rows:
            d = dict(r)
            d['status'] = parse_status(d.get('content', ''))
            # Don't send full content to frontend
            del d['content']
            agents.append(d)

        return jsonify(agents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/groups')
def get_groups(session_id):
    """Get task groups for a session."""
    conn = None
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, name, status, assigned_to, complexity,
                   revision_count, last_review_status, feature_branch
            FROM task_groups
            WHERE session_id = ?
            ORDER BY created_at
        """, (session_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/logs')
def get_logs(session_id):
    """Get recent orchestration logs (interactions only)."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    conn = None

    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, timestamp, agent_type, agent_id, iteration,
                   SUBSTR(content, 1, 500) as content_preview
            FROM orchestration_logs
            WHERE session_id = ? AND log_type = 'interaction'
            ORDER BY datetime(timestamp) DESC
            LIMIT ? OFFSET ?
        """, (session_id, limit, offset)).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/agent/<path:agent_type>/reasoning')
def get_reasoning(session_id, agent_type):
    """Get reasoning entries for a specific agent."""
    group_id = request.args.get('group_id')
    conn = None

    try:
        conn = get_db()

        query = """
            SELECT id, timestamp, reasoning_phase, confidence_level,
                   content, group_id, references_json, agent_id
            FROM orchestration_logs
            WHERE session_id = ? AND agent_type = ? AND log_type = 'reasoning'
        """
        params = [session_id, agent_type]

        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)

        query += " ORDER BY datetime(timestamp) ASC LIMIT 50"

        rows = conn.execute(query, params).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/agent/<path:agent_type>/logs')
def get_agent_logs(session_id, agent_type):
    """Get all logs for a specific agent (both interactions and reasoning)."""
    limit = request.args.get('limit', 50, type=int)
    conn = None

    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, timestamp, log_type, reasoning_phase, confidence_level,
                   content, group_id, agent_id
            FROM orchestration_logs
            WHERE session_id = ? AND agent_type = ?
            ORDER BY datetime(timestamp) ASC
            LIMIT ?
        """, (session_id, agent_type, limit)).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/session/<session_id>/stats')
def get_session_stats(session_id):
    """Get summary statistics for a session."""
    conn = None
    try:
        conn = get_db()

        # Get session info
        session = conn.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,)).fetchone()

        # Get agent counts
        agent_stats = conn.execute("""
            SELECT agent_type, COUNT(*) as log_count
            FROM orchestration_logs
            WHERE session_id = ?
            GROUP BY agent_type
        """, (session_id,)).fetchall()

        # Get total tokens
        token_total = conn.execute("""
            SELECT COALESCE(SUM(tokens_estimated), 0) as total
            FROM token_usage WHERE session_id = ?
        """, (session_id,)).fetchone()

        # Get task group summary
        group_stats = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM task_groups
            WHERE session_id = ?
            GROUP BY status
        """, (session_id,)).fetchall()

        return jsonify({
            "session": dict(session) if session else None,
            "agent_stats": {r['agent_type']: r['log_count'] for r in agent_stats},
            "total_tokens": token_total['total'] if token_total else 0,
            "group_stats": {r['status']: r['count'] for r in group_stats}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f"""
    ====================================
      BAZINGA Mini Dashboard
    ====================================

    Server running at: http://localhost:{port}
    Database path: {DB_PATH}

    Press Ctrl+C to stop
    """)

    app.run(host=host, port=port, debug=False, threaded=True)
