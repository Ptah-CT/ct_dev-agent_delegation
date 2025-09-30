# Logfire Configuration

## Setup

### Environment Variable
```bash
export LOGFIRE_TOKEN=your_logfire_token_here
```

### Using secrets.env
```bash
# Load secrets
source secrets.env

# Or use in shell
export $(cat secrets.env | xargs)
```

### Permanent Setup (Optional)
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export LOGFIRE_TOKEN=your_logfire_token_here' >> ~/.bashrc
source ~/.bashrc
```

## Testing

```bash
# Test configuration
python3 -c "import logfire; logfire.configure(); logfire.info('Test')"

# Run server with Logfire
export LOGFIRE_TOKEN=your_logfire_token_here
python3 -m ct_dev_agent_orchestrator_mcp
```

## Development vs Production

**Development** (without token):
- Logfire wird automatisch deaktiviert
- Logs gehen an stderr
- Kein externes Monitoring

**Production** (with token):
- Logfire sendet Logs an Dashboard
- Monitoring und Alerts aktiv
- Performance Tracking verfügbar

## Logfire Dashboard

Nach Konfiguration verfügbar unter:
https://logfire.pydantic.dev/

Filter nach:
- `component="agent_orchestrator"`
- `component="opencode_service"`
- `component="session_manager"`

## Security

⚠️ **WICHTIG**: Token niemals committen!

Das Token ist bereits in `.gitignore`:
```
secrets.env
*.env
.env
```

Bei versehentlichem Commit:
1. Token sofort rotieren in Logfire Dashboard
2. Git History cleanen: `git filter-branch`
3. Neues Token generieren

## Monitoring Queries

### Active Sessions
```python
logfire.info("Session created", session_id=..., agent_role=...)
```

### Agent Lifecycle
```python
logfire.info("Agent spawned", agent_id=..., port=...)
logfire.error("Agent failed", agent_id=..., error=...)
```

### Performance
```python
logfire.info("Operation completed", duration=..., operation=...)
```

---

**Token Type**: Production
**Created**: 2024-09-30
**Scope**: Full access
