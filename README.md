# ct_dev-agent_orchestrator-mcp

MCP Server for orchestrating ct_dev-agents through OpenCode.ai integration.

## 🜄 Purpose

Enables the Main Agent (Claude via OpenCode.ai) to delegate work to specialized ct_dev-agents in an asynchronous, non-blocking manner. Each agent runs as a separate OpenCode server instance with custom instructions.

## Features

- **Fire-and-Forget Delegation**: Immediate response (<100ms) for non-blocking agent assignment
- **Agent Pool Management**: Automatic creation and lifecycle management of agent instances
- **OpenCode Integration**: Starts and manages `opencode serve` instances for each agent
- **Health Monitoring**: Background health checks for all agent instances
- **Task Integration**: Works with ct_dev-task_orchestrator for task tracking
- **Logfire Integration**: Centralized logging and monitoring

## Agent Roles

18 specialized agent roles are available (based on `~/.claude/agents/`):

- backend_specialist
- bug_hunter
- code_reviewer
- database_architect
- devops_engineer
- documentation_specialist
- frontend_specialist
- generic_engineer
- integration_specialist
- performance_engineer
- product_manager
- project_architect
- quality_assurance
- refactoring_specialist
- research_specialist
- security_expert
- system_architect
- technical_writer

## Installation

```bash
cd /home/auctor/dev/ct_dev-agent_orchestrator-mcp
pip install -e .
```

## Configuration

Add to your MCP settings (e.g., `~/.config/opencode/mcp_settings.json`):

```json
{
  "mcpServers": {
    "ct_dev-agent_orchestrator": {
      "command": "python",
      "args": ["-m", "ct_dev_agent_orchestrator_mcp.server"],
      "env": {
        "LOGFIRE_TOKEN": "your-token-here"
      }
    }
  }
}
```

Or use with environment file:

```bash
# Load secrets
source /home/auctor/secrets.env

# Start server
python -m ct_dev_agent_orchestrator_mcp.server
```

## Usage

### Delegate Work

```python
# Via MCP tool
delegate_work(
    task_id="550e8400-e29b-41d4-a716-446655440000",
    agent_role="backend_specialist",
    instructions="Implement OAuth2 authentication endpoints",
    context={"framework": "FastAPI"},
    timeout_seconds=7200
)
# Returns: delegation_id for tracking
```

### Check Status

```python
get_delegation_status(
    delegation_id="delegation-uuid"
)
```

### Get Result

```python
get_delegation_result(
    delegation_id="delegation-uuid"
)
```

### List Agents

```python
list_agents()
# Shows all active agent instances
```

### Cancel Delegation

```python
cancel_delegation(
    delegation_id="delegation-uuid"
)
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Main Agent (Claude via OpenCode.ai)                │
└───────────────────┬─────────────────────────────────┘
                    │ MCP Protocol
┌───────────────────▼─────────────────────────────────┐
│ ct_dev-agent_orchestrator-mcp                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ AgentManager (Lifecycle & Pool)                 │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ DelegationService (Work Assignment)             │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ OpenCodeService (Instance Management)           │ │
│ └─────────────────────────────────────────────────┘ │
└───────────────────┬─────────────────────────────────┘
                    │ opencode serve --custom-instructions
                    ├─────────────────┬──────────────────┬─────
                    ▼                 ▼                  ▼
            ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
            │ Agent 1       │ │ Agent 2       │ │ Agent N       │
            │ Port: 8000    │ │ Port: 8001    │ │ Port: 800N    │
            │ backend_spec  │ │ frontend_spec │ │ ...           │
            └───────────────┘ └───────────────┘ └───────────────┘
```

## Design Principles (X^∞)

- **Fail Fast**: No retries, binary success/failure
- **Atomic Delegation**: Single responsibility per delegation
- **Async First**: Non-blocking operations, immediate responses
- **No Docker**: Direct host system execution (Debian)
- **Centralized Logging**: All activity logged to Logfire

## Development

### Run Tests

```bash
pytest tests/
```

### Project Structure

```
src/ct_dev_agent_orchestrator_mcp/
├── __init__.py
├── server.py                    # MCP server main
├── models/
│   ├── __init__.py
│   ├── agent.py                # Agent data models
│   ├── delegation.py           # Delegation models
│   └── task_context.py         # Task scope models
├── services/
│   ├── __init__.py
│   ├── agent_manager.py        # Agent lifecycle
│   ├── delegation_service.py   # Work delegation
│   └── opencode_service.py     # OpenCode integration
├── handlers/                    # Future: Event handlers
└── utils/                       # Future: Utilities
```

## References

- Specification: `/specs/001-agent-orchestrator/spec.md`
- Planning: `PLANUNG.md`
- X^∞ Constitution: `/home/auctor/CLAUDE.md`

## License

Internal use only - ct_dev project
