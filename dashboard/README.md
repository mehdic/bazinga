# BAZINGA Dashboard

Real-time orchestration monitoring dashboard with WebSocket updates.

## Quick Start

### Automatic (Recommended)

The dashboard and its dependencies are automatically installed when you run:

```bash
# Initial setup (installs dashboard dependencies automatically)
bazinga init --here

# Or update existing installation (updates dashboard dependencies)
bazinga update
```

The dashboard server then starts automatically when you initialize orchestration:

```bash
./scripts/init-orchestration.sh
```

### Manual Dependency Installation

If you need to install or reinstall dependencies manually:

```bash
# Option 1: Use CLI command (with confirmation)
bazinga setup-dashboard

# Option 2: Install directly with pip
cd dashboard
pip3 install -r requirements.txt
```

### Manual Start

```bash
cd dashboard
python3 server.py
```

Server runs on: **http://localhost:53124**

## Features

- ✅ Real-time WebSocket updates
- 📊 Workflow visualization (Mermaid diagrams)
- 👥 Agent status tracking
- 💬 Communication history
- 📈 Quality metrics
- 🤖 AI-powered diagrams (optional)

## Configuration

### Enable AI Diagram Feature

Edit `coordination/skills_config.json`:

```json
{
  "dashboard": {
    "dashboard_ai_diagram_enabled": true
  }
}
```

Set API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Restart the dashboard server.

## Managing the Dashboard

Use the dashboard management script:

```bash
cd dashboard

# Start
./dashboard.sh start

# Stop
./dashboard.sh stop

# Restart
./dashboard.sh restart

# Check status
./dashboard.sh status

# View logs
./dashboard.sh logs
```

Or manually:

```bash
# Stop
kill $(cat /tmp/bazinga-dashboard.pid)

# View logs
tail -f /tmp/bazinga-dashboard.log
```

## Documentation

Full documentation: `/research/dashboard-feature.md`

## Troubleshooting

**Port already in use:**
```bash
# Change port to a different one
export DASHBOARD_PORT=9000
python3 server.py
```

**Dependencies missing:**
```bash
pip3 install -r requirements.txt
```

**WebSocket not connecting:**
- Check browser console for errors
- Verify firewall settings
- Dashboard will fall back to polling
