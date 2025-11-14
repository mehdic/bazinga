#!/usr/bin/env python3
"""
Automatic Agent Response Logger
Wraps agent spawning with automatic database logging and validation.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import the database client
from bazinga_db import BazingaDB


class AutoLogger:
    """Automatically logs agent responses with validation."""

    def __init__(self, db_path: str, session_id: str):
        self.db = BazingaDB(db_path)
        self.session_id = session_id
        self.logs_saved = 0
        self.logs_failed = 0

    def log_agent_response(
        self,
        agent_type: str,
        content: str,
        iteration: Optional[int] = None,
        agent_id: Optional[str] = None,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Log agent response with automatic validation.

        Returns:
            Dict with success status and verification details
        """
        try:
            # Log the interaction
            result = self.db.log_interaction(
                session_id=self.session_id,
                agent_type=agent_type,
                content=content,
                iteration=iteration,
                agent_id=agent_id
            )

            self.logs_saved += 1

            if verify:
                # Additional verification: query back from database
                logs = self.db.get_logs(
                    self.session_id,
                    limit=1,
                    agent_type=agent_type
                )

                if not logs or logs[0]['id'] != result['log_id']:
                    raise RuntimeError("Verification failed: logged entry not found in database")

            return {
                'status': 'success',
                'verified': verify,
                'details': result,
                'stats': {
                    'logs_saved': self.logs_saved,
                    'logs_failed': self.logs_failed
                }
            }

        except Exception as e:
            self.logs_failed += 1
            return {
                'status': 'error',
                'error': str(e),
                'agent_type': agent_type,
                'stats': {
                    'logs_saved': self.logs_saved,
                    'logs_failed': self.logs_failed
                }
            }

    def get_stats(self) -> Dict[str, int]:
        """Get logging statistics."""
        return {
            'logs_saved': self.logs_saved,
            'logs_failed': self.logs_failed,
            'success_rate': (self.logs_saved / (self.logs_saved + self.logs_failed) * 100)
                           if (self.logs_saved + self.logs_failed) > 0 else 0
        }

    def verify_session_logs(self) -> Dict[str, Any]:
        """Verify all logs for current session."""
        logs = self.db.get_logs(self.session_id, limit=1000)

        agent_counts = {}
        for log in logs:
            agent_type = log['agent_type']
            agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1

        return {
            'session_id': self.session_id,
            'total_logs': len(logs),
            'by_agent_type': agent_counts,
            'earliest': logs[-1]['timestamp'] if logs else None,
            'latest': logs[0]['timestamp'] if logs else None
        }


def main():
    """Command-line interface for auto logger."""
    if len(sys.argv) < 5:
        print("Usage: auto_logger.py <db_path> <session_id> <agent_type> <content> [iteration] [agent_id]")
        sys.exit(1)

    db_path = sys.argv[1]
    session_id = sys.argv[2]
    agent_type = sys.argv[3]
    content = sys.argv[4]
    iteration = int(sys.argv[5]) if len(sys.argv) > 5 else None
    agent_id = sys.argv[6] if len(sys.argv) > 6 else None

    logger = AutoLogger(db_path, session_id)
    result = logger.log_agent_response(agent_type, content, iteration, agent_id)

    print(json.dumps(result, indent=2))

    if result['status'] != 'success':
        sys.exit(1)


if __name__ == '__main__':
    main()
