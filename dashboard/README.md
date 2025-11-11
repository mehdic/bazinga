# BAZINGA Dashboard

Real-time orchestration monitoring dashboard with WebSocket updates.

## Quick Start

### Automatic (Recommended)

The dashboard starts automatically when you initialize orchestration:

```bash
cd /home/user/bazinga
./scripts/init-orchestration.sh
```

### Manual Start

```bash
cd dashboard

# Install dependencies (first time only)
pip3 install -r requirements.txt

# Start server
python3 server.py
```

Server runs on: **http://localhost:8080**

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

## Stopping the Server

```bash
kill $(cat /tmp/bazinga-dashboard.pid)
```

## Logs

```bash
tail -f /tmp/bazinga-dashboard.log
```

## Documentation

Full documentation: `/research/dashboard-feature.md`

## Troubleshooting

**Port already in use:**
```bash
# Change port
export DASHBOARD_PORT=8081
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
