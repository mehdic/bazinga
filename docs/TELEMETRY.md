# BAZINGA Anonymous Telemetry

BAZINGA CLI includes anonymous telemetry to help track installation and upgrade statistics.

## What is Tracked?

The telemetry system sends minimal, anonymous data when users:
- Install BAZINGA (`bazinga init`)
- Upgrade BAZINGA (`bazinga update`)

**Data sent:**
```json
{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "command": "init",
    "version": "1.1.0",
    "timestamp": "2025-11-12T10:30:45.123456"
}
```

## Privacy & Security

✅ **What we collect:**
- A random UUID (generated on first use)
- Command name (`init` or `update`)
- BAZINGA version
- Timestamp

❌ **What we DON'T collect:**
- IP addresses (intentionally not logged)*
- Machine names or hostnames
- Usernames or email addresses
- Project names or code
- Any personal information

*Note: Your web server logs may capture IP addresses at the infrastructure level. This is separate from the telemetry payload.

## How It Works

1. **First Installation:** When a user runs `bazinga init`, a UUID is generated and stored locally in `~/.bazinga/telemetry_id.json`
2. **Subsequent Uses:** The same UUID is used for all future tracking
3. **HTTP Request:** A POST request is sent to your tracking endpoint
4. **Non-Blocking:** Runs in a background thread with 2s timeout
5. **Fail-Safe:** If the request fails, it fails silently without affecting the CLI

## Setting Up Your Tracking Endpoint

### Option 1: Simple Flask Server

```python
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# In-memory storage (replace with database for production)
installations = {}

@app.route('/track', methods=['POST'])
def track():
    data = request.json

    uuid = data['uuid']
    command = data['command']
    version = data['version']
    timestamp = data['timestamp']

    # Track unique installations
    if uuid not in installations:
        installations[uuid] = {
            'first_seen': timestamp,
            'commands': []
        }

    installations[uuid]['commands'].append({
        'command': command,
        'version': version,
        'timestamp': timestamp
    })

    # Log to console
    print(f"[{timestamp}] {command} - UUID: {uuid} - Version: {version}")
    print(f"Total unique installations: {len(installations)}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Option 2: Save to File

```python
from flask import Flask, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)
TRACKING_FILE = Path("telemetry.jsonl")

@app.route('/track', methods=['POST'])
def track():
    data = request.json

    # Append to JSONL file
    with open(TRACKING_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Option 3: Use Existing Analytics Services

You can forward the data to services like:
- **PostHog** (open-source analytics)
- **Mixpanel**
- **Amplitude**
- **Google Analytics**
- **Custom database** (PostgreSQL, MongoDB, etc.)

Example with PostHog:

```python
from flask import Flask, request, jsonify
import posthog

posthog.project_api_key = 'your-project-key'
posthog.host = 'https://app.posthog.com'

app = Flask(__name__)

@app.route('/track', methods=['POST'])
def track():
    data = request.json

    posthog.capture(
        distinct_id=data['uuid'],
        event=f"bazinga_{data['command']}",
        properties={
            'version': data['version'],
            'timestamp': data['timestamp']
        }
    )

    return jsonify({"status": "ok"}), 200
```

## Configuring the Endpoint

### Method 1: Edit the Source Code

Edit `src/bazinga_cli/telemetry.py` and update the `DEFAULT_ENDPOINT`:

```python
DEFAULT_ENDPOINT = "https://your-domain.com/api/track"
```

### Method 2: Use Environment Variable (Future Enhancement)

You could modify the code to support:

```python
import os

DEFAULT_ENDPOINT = os.getenv(
    "BAZINGA_TELEMETRY_URL",
    "https://your-domain.com/api/track"
)
```

## Analyzing Your Data

Once you're collecting data, you can analyze:

### Total Unique Installations
```bash
# If using JSONL file
cat telemetry.jsonl | jq -r .uuid | sort -u | wc -l
```

### Installations Over Time
```bash
# Group by date
cat telemetry.jsonl | jq -r '.timestamp[:10]' | sort | uniq -c
```

### Version Distribution
```bash
# Which versions are most popular?
cat telemetry.jsonl | jq -r .version | sort | uniq -c | sort -rn
```

### Command Distribution
```bash
# How many init vs update?
cat telemetry.jsonl | jq -r .command | sort | uniq -c
```

## Testing Telemetry

You can test the telemetry locally:

```bash
# Start a test server
python3 -m flask run --port 5000

# In the test server script:
from flask import Flask, request
app = Flask(__name__)

@app.route('/track', methods=['POST'])
def track():
    print("Received:", request.json)
    return {"status": "ok"}, 200
```

Then update the endpoint to `http://localhost:5000/track` and run `bazinga init`.

## Disabling Telemetry (Future Enhancement)

Currently, telemetry is always enabled but fails silently if the endpoint is unreachable.

To add opt-out support, you could:

1. Check for an environment variable: `BAZINGA_TELEMETRY=0`
2. Check for a config file: `~/.bazinga/config.json` with `{"telemetry": false}`
3. Add a CLI flag: `bazinga init --no-telemetry`

## Questions?

If you have questions about the telemetry implementation, please open an issue on the BAZINGA GitHub repository.
