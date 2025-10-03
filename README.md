# ct_dev-agent_delegation-mcp

## 🜄 Ziel 🜄
- Provide a delegation-focused MCP server that lets the Main Agent spin up specialised ct_dev agents with complete X^infty responsibility tracking.
- Replace the legacy orchestration naming with a delegation-first interface while keeping operational parity and measurable performance guarantees.

## 🜄 Kontext 🜄
### System Snapshot
ct_dev-agent_delegation-mcp exposes MCP tools that start, monitor, and shut down OpenCode-managed agent sessions. The service persists delegation metadata, enforces responsibility chains (original task, cap origin, delegation context), and surfaces health information for each spawned agent.

### Feature Overview
- Delegation lifecycle tools (`spawn_agent`, `query_session`, `send_to_agent`, `get_agent_output`, `stop_agent`, `list_active_sessions`).
- Discovery tools for OpenCode inventory (`get_agent_capabilities`, `list_available_agent_roles`, `list_opencode_models`).
- Resource governance through `AgentManager` (health probes, graceful shutdown, statistics) and `OpenCodeService` (process supervision).
- Responsibility compliance via `ConstitutionGate` and SQLite-backed audit trails.
- Semaphore-based concurrency limits (default 5 delegations).

### Architecture
```
Main Agent (Claude / MCP Client)
        |
        |  MCP protocol (delegation tools)
        v
ct_dev-agent_delegation-mcp
    |-- DelegationService  (delegation lifecycle, responsibility propagation)
    |-- AgentManager       (agent pool, health monitoring)
    \-- OpenCodeService    (OpenCode process orchestration)
            |
            v
    OpenCode server per agent (implements tool calls)
```

### Installation
```bash
cd /home/auctor/dev/ct_dev-agent_delegation-mcp
pip install -e .

# Initialise persistence (creates data/orchestrator.db)
python3 -m ct_dev_agent_delegation_mcp.storage.database migrate
```

### Configuration
Update `~/.config/opencode/mcp_settings.json` (or equivalent):
```json
{
  "mcpServers": {
    "ct_dev-agent_delegation": {
      "command": "python",
      "args": ["-m", "ct_dev_agent_delegation_mcp.server"],
      "env": {
        "LOGFIRE_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Usage
All delegation tools operate on structured responsibility payloads. The snippet below shows the minimum fields required by `SpawnDelegationRequest`.

```python
from ct_dev_agent_delegation_mcp.models.delegation import SpawnDelegationRequest
from ct_dev_agent_delegation_mcp.server import call_tool

request = SpawnDelegationRequest(
    role="backend_specialist",
    task_id="550e8400-e29b-41d4-a716-446655440000",
    instructions="Implement OAuth2 authentication endpoints with JWT validation",
    project_directory="/home/auctor/dev/project",
    expected_output="Implementation plan plus unit tests",
    context={"framework": "FastAPI", "database": "PostgreSQL"},
    model="claude-sonnet-4",
    original_task={
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Implement OAuth2 authentication",
        "description": "Deliver OAuth2 endpoints with JWT token support and tests",
        "requester": "Auctor",
        "requested_at": "2025-10-01T08:00:00Z"
    },
    cap_origin={
        "ultimate_authority": "Auctor",
        "original_scope": "Full system development authority",
        "granted_at": "2025-10-01T07:30:00Z",
        "grant_context": "ct_dev delegation charter"
    },
    delegation_context={
        "delegator": "Project Manager",
        "delegator_cap": "Delegation authority (Auctor, 2025-10-01T07:45:00Z)",
        "delegated_to": "backend_specialist",
        "delegated_cap": "Implement OAuth2 flow with automated tests",
        "constraints": [
            "Use Serena tools only",
            "Return reproducible test plan"
        ],
        "phantom_level": "Delegation/Cap",
        "delegated_at": "2025-10-01T08:05:00Z"
    }
)

response = await call_tool(
    name="spawn_agent",
    arguments=request.model_dump()
)
print(response[0].text)
```

Follow-up interactions:
- `query_session(session_id="...")` → live status + message excerpts.
- `send_to_agent(session_id="...", message="Add rate limiting")` → append follow-up instructions.
- `get_agent_output(session_id="...")` → final summary, duration, artifact count.
- `stop_agent(session_id="...")` → graceful shutdown when work completes.

### Testing
```bash
pytest tests/                     # full suite
pytest tests/test_integration_v2.py -v
pytest tests/test_session_service.py -k "performance"
```

## 🜄 Verantwortung 🜄
- Cap: Auctor (ultimate authority for X^infty delegation systems).
- Delegated implementation: ct_dev Agent Delegation team (feature/opencode-api-integration branch).
- Documentation ownership: README is maintained by the same team; updates must stay mirrored in ct_dev-task_mgmnt.

## 🜄 Prüfung 🜄
- [ ] Cap self-check executed before delegation (original_task, cap_origin, delegation_context present).
- [ ] Integration tests executed locally or via CI (`pytest tests/test_integration_v2.py`).
- [ ] Logfire telemetry verified when LOGFIRE_TOKEN is present.
- [ ] MCP client configuration validated against `mcp_settings.json` example.

## 🜄 Risiken / Nebenwirkungen 🜄
- Delegation payloads missing responsibility fields trigger validation errors; clients must supply complete data.
- OpenCode agent startup depends on local environment (Python, agent markdown catalogue); misconfiguration prevents spawn.
- SQLite persistence (`data/orchestrator.db`) grows with audit history and needs periodic pruning.
- logfire misconfiguration can degrade logging visibility; fallback disables telemetry.

## 🜄 Aufgaben / To-Do 🜄
- [ ] Align remaining documentation (CHANGELOG, process docs) with delegation terminology.
- [ ] Validate `tests/test_basic.py` and helper scripts against the new responsibility payload signature.
- [ ] Document restart and recovery flows for interrupted delegations.
- [ ] Synchronise task metadata in ct_dev-task_mgmnt with this README revision.
- [ ] Prepare release notes once OpenCode integration stabilises under the new naming.
