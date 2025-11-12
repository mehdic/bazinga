"""
Anonymous telemetry module for BAZINGA CLI.

Tracks installation and usage statistics without collecting personal information.
Only sends: unique UUID, command name, version, and timestamp.

## Setup Instructions

To receive telemetry data, you need to:

1. Set up a simple HTTP endpoint that accepts POST requests
2. Update the DEFAULT_ENDPOINT in this file with your URL
3. The endpoint will receive JSON payloads like:
   {
       "uuid": "550e8400-e29b-41d4-a716-446655440000",
       "command": "init",
       "version": "1.1.0",
       "timestamp": "2025-11-12T10:30:45.123456"
   }

## Example Endpoint (Python/Flask)

    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route('/track', methods=['POST'])
    def track():
        data = request.json
        # Log to database, file, or analytics service
        print(f"Installation: {data['uuid']} - {data['command']} v{data['version']}")
        return jsonify({"status": "ok"}), 200

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

## Privacy

- No IP addresses are stored (though web server logs may capture them)
- No machine names, usernames, or personal information
- Only a random UUID for counting unique installations
- Telemetry runs in a background thread with 2s timeout
- Failures are silent - never breaks the CLI
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from threading import Thread

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class AnonymousTelemetry:
    """Handles anonymous usage telemetry for BAZINGA CLI."""

    # TODO: Replace with your actual telemetry endpoint URL
    # Example: "https://your-domain.com/api/track"
    # Or use environment variable: os.getenv("BAZINGA_TELEMETRY_URL", "https://default-url.com/track")
    DEFAULT_ENDPOINT = "https://your-telemetry-endpoint.com/track"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize telemetry handler.

        Args:
            config_dir: Directory to store the UUID config file.
                       Defaults to ~/.bazinga/
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".bazinga"
        else:
            self.config_dir = config_dir

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.uuid_file = self.config_dir / "telemetry_id.json"
        self.enabled = True  # Can be made configurable

    def get_or_create_uuid(self) -> str:
        """Get existing UUID or create a new one."""
        if self.uuid_file.exists():
            try:
                with open(self.uuid_file, 'r') as f:
                    data = json.load(f)
                    return data.get('uuid', self._create_new_uuid())
            except (json.JSONDecodeError, IOError):
                return self._create_new_uuid()
        else:
            return self._create_new_uuid()

    def _create_new_uuid(self) -> str:
        """Create and save a new UUID."""
        new_uuid = str(uuid.uuid4())
        data = {
            'uuid': new_uuid,
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

        try:
            with open(self.uuid_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Fail silently - telemetry shouldn't break the CLI

        return new_uuid

    def track_event(
        self,
        command: str,
        version: str,
        endpoint: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> None:
        """
        Track a CLI command event asynchronously.

        Args:
            command: The command being executed (e.g., "init", "update")
            version: BAZINGA CLI version
            endpoint: Custom tracking endpoint URL (optional)
            extra_data: Additional anonymous data to send (optional)
        """
        if not self.enabled or not HTTPX_AVAILABLE:
            return

        # Run in background thread so it doesn't block CLI
        thread = Thread(
            target=self._send_telemetry,
            args=(command, version, endpoint, extra_data),
            daemon=True
        )
        thread.start()

    def _send_telemetry(
        self,
        command: str,
        version: str,
        endpoint: Optional[str],
        extra_data: Optional[dict]
    ) -> None:
        """
        Send telemetry data to the endpoint.

        This runs in a background thread and fails silently.
        """
        try:
            user_uuid = self.get_or_create_uuid()

            payload = {
                'uuid': user_uuid,
                'command': command,
                'version': version,
                'timestamp': datetime.utcnow().isoformat()
            }

            if extra_data:
                payload.update(extra_data)

            url = endpoint or self.DEFAULT_ENDPOINT

            # Send with short timeout - don't wait too long
            with httpx.Client(timeout=2.0) as client:
                client.post(url, json=payload)

        except Exception:
            # Fail silently - telemetry should never break the CLI
            pass


# Global telemetry instance
_telemetry_instance: Optional[AnonymousTelemetry] = None


def get_telemetry() -> AnonymousTelemetry:
    """Get or create the global telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = AnonymousTelemetry()
    return _telemetry_instance


def track_command(command: str, version: str, endpoint: Optional[str] = None) -> None:
    """
    Convenience function to track a command execution.

    Args:
        command: The command being executed
        version: BAZINGA CLI version
        endpoint: Custom tracking endpoint (optional)
    """
    telemetry = get_telemetry()
    telemetry.track_event(command, version, endpoint)
