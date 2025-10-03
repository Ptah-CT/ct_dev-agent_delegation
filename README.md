# ct_dev-agent_delegation-mcp

MCP Server for delegating work to ct_dev-agents through OpenCode.ai integration with delegation-based architecture.

## 🜄 Purpose

Enables the Main Agent (Claude via OpenCode.ai) to delegate work to specialized ct_dev-agents through interactive sessions. Each agent runs as a separate OpenCode server instance with custom instructions, supporting real-time communication and follow-up messaging for iterative work.

## Features

- **Delegation-Based Architecture**: Interactive agent sessions with follow-up message support
- **Real-time Delegation Tracking**: Monitor delegation status, output, and completion
- **Concurrent Delegation Management**: Semaphore-limited (5 concurrent delegations) for resource control
- **Performance Optimized**: <1s delegation creation, >5 messages/second throughput
- **Agent Pool Management**: Automatic creation and lifecycle management of agent instances
- **OpenCode Integration**: Starts and manages `opencode serve` instances for each agent
- **Task Integration**: Works with ct_dev-task_mgmnt for task tracking
- **Logfire Integration**: Centralized logging and monitoring
- **SQLite Persistence**: State management for delegations, agents, and audit trail
- **Constitution Gates**: Validates operations against X^∞ principles before execution
- **Audit Trail**: Complete responsibility tracking for all delegation events

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
cd /home/auctor/dev/ct_dev-agent_delegation-mcp
pip install -e .

# Initialize database
python3 -m ct_dev_agent_delegation_mcp.storage.database migrate
```

## Configuration

Add to your MCP settings (e.g., `~/.config/opencode/mcp_settings.json`):

```json
{
  "mcpServers": {
    "ct_dev-agent_orchestrator": {
      "command": "python",
      "args": ["-m", "ct_dev_agent_delegation_mcp.server"],
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
python -m ct_dev_agent_delegation_mcp.server
```

## Usage

### V2 Session-Based API

#### 1. Spawn Agent Session

Create a new interactive agent delegation:

```python
spawn_agent(
    role="backend_specialist",
    task_id="550e8400-e29b-41d4-a716-446655440000",
    instructions="Implement OAuth2 authentication endpoints with JWT token validation",
    context={"framework": "FastAPI", "auth_provider": "Auth0"},
    model="claude-sonnet-4"
)
# Returns: session_id (e.g., "session-uuid")
# Response time: <1s
```

#### 2. Query Session Status

Get real-time session status and metadata:

```python
query_session(
    session_id="session-uuid"
)
# Returns: {
#   "status": "running" | "completed" | "error",
#   "role": "backend_specialist",
#   "created_at": "2025-09-30T10:00:00Z",
#   "updated_at": "2025-09-30T10:05:00Z",
#   "message_count": 3
# }
```

#### 3. Send Follow-up Message

Send additional instructions to running session:

```python
send_to_agent(
    session_id="session-uuid",
    message="Please add rate limiting (100 requests/minute) to all authentication endpoints"
)
# Returns: message_id for tracking
# Supports iterative refinement of work
```

#### 4. Get Agent Output

Retrieve session output and results:

```python
get_agent_output(
    session_id="session-uuid"
)
# Returns: {
#   "messages": [
#     {"role": "user", "content": "...", "timestamp": "..."},
#     {"role": "agent", "content": "...", "timestamp": "..."}
#   ],
#   "final_result": "...",
#   "artifacts": [...]
# }
```

#### 5. List Active Sessions

View all currently active sessions:

```python
list_active_sessions()
# Returns: [
#   {
#     "session_id": "session-uuid-1",
#     "role": "backend_specialist",
#     "status": "running",
#     "created_at": "..."
#   },
#   {
#     "session_id": "session-uuid-2",
#     "role": "frontend_specialist",
#     "status": "completed",
#     "created_at": "..."
#   }
# ]
```

#### 6. Stop Agent Session

Gracefully terminate a session:

```python
stop_agent(
    session_id="session-uuid"
)
# Cleans up resources, saves state
# Returns: final session status
```

#### 7. Get Agent Capabilities

Query available agent roles and their capabilities:

```python
get_agent_capabilities()
# Returns: {
#   "roles": ["backend_specialist", "frontend_specialist", ...],
#   "max_concurrent_sessions": 5,
#   "supported_models": ["claude-sonnet-4", "claude-opus-4"],
#   "features": ["follow_up_messages", "real_time_tracking", ...]
# }
```

### Management Tools

#### List Active Agents

View all agent instances:

```python
list_agents()
# Shows all active agent instances with health status
# Returns: [
#   {
#     "agent_id": "agent-uuid",
#     "role": "backend_specialist",
#     "port": 8000,
#     "status": "healthy",
#     "sessions": 2
#   }
# ]
```

#### Get Agent Statistics

Retrieve performance metrics:

```python
get_agent_stats()
# Returns: {
#   "total_sessions": 147,
#   "active_sessions": 3,
#   "avg_session_duration": "5m 32s",
#   "success_rate": 0.95,
#   "messages_per_session": 4.2
# }
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Main Agent (Claude via MCP Client)                 │
└───────────────────┬─────────────────────────────────┘
                    │ MCP Protocol (V2 Delegation Tools)
┌───────────────────▼─────────────────────────────────┐
│ ct_dev-agent_delegation-mcp (V2)                  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ DelegationService (Delegation Lifecycle)              │ │
│ │ - spawn_agent, query_session                    │ │
│ │ - send_to_agent, get_agent_output              │ │
│ │ - stop_agent, list_active_sessions             │ │
│ │ - get_agent_capabilities                        │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ AgentManager (Instance Management)              │ │
│ │ - Agent pool lifecycle                          │ │
│ │ - Health monitoring                             │ │
│ │ - Resource allocation                           │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ OpenCodeService (OpenCode API Integration)      │ │
│ │ - Instance creation/cleanup                     │ │
│ │ - Message routing                               │ │
│ └─────────────────────────────────────────────────┘ │
└───────────────────┬─────────────────────────────────┘
                    │ OpenCode Server API
                    ├─────────────────┬──────────────────
                    ▼                 ▼                  
            ┌───────────────┐ ┌───────────────┐ 
            │ Delegation 1     │ │ Delegation 2     │ 
            │ backend_spec  │ │ frontend_spec │ 
            │ Interactive   │ │ Interactive   │ 
            │ Port: 8000    │ │ Port: 8001    │ 
            └───────────────┘ └───────────────┘ 
```

## Version 2 (Delegation-Based Architecture)

V2 represents a complete architectural shift from delegation-based to session-based agent orchestration:

### Key Changes

- **Interactive Sessions**: Replaces fire-and-forget delegation with persistent sessions
- **Follow-up Messaging**: Support for iterative work and refinement
- **Real-time Tracking**: Query session status and output at any time
- **Improved Concurrency**: Semaphore-based management (5 concurrent delegations)
- **Performance Optimizations**: 
  - Session creation: <1s
  - Message throughput: >5 msg/s
  - Resource cleanup: Automatic

### Migration from V1

V1 delegation tools have been deprecated and removed. V2 provides equivalent functionality with enhanced interactivity:

| V1 Tool | V2 Equivalent | Enhancement |
|---------|---------------|-------------|
| `delegate_work` | `spawn_agent` | Returns session_id for interactive work |
| `get_delegation_status` | `query_session` | Real-time status with detailed metadata |
| `get_delegation_result` | `get_agent_output` | Full message history + artifacts |
| `list_delegations` | `list_active_sessions` | Shows all sessions with status |
| `cancel_delegation` | `stop_agent` | Graceful cleanup with state preservation |
| N/A | `send_to_agent` | NEW: Follow-up message support |
| N/A | `get_agent_capabilities` | NEW: Query available roles |

### V2 Testing

All 74 tests passing:
- Integration tests: `tests/test_integration_v2.py`
- Unit tests: `tests/test_session_service.py`
- Performance tests: Session creation, message throughput

See `V2_MIGRATION_TASKS.md` for detailed migration documentation.

## Design Principles (X^∞)

- **Fail Fast**: No retries, binary success/failure
- **Atomic Sessions**: Single responsibility per session
- **Interactive First**: Support for follow-up messages and refinement
- **Resource Management**: Semaphore-based concurrency control
- **No Docker**: Direct host system execution (Debian)
- **Centralized Logging**: All activity logged to Logfire

## Development

### Run Tests

```bash
# All tests
pytest tests/

# V2 integration tests
pytest tests/test_integration_v2.py -v

# Performance tests
pytest tests/test_session_service.py -v -k performance
```

### Project Structure

```
src/ct_dev_agent_delegation_mcp/
├── __init__.py
├── server.py                    # MCP server main (V2 tools)
├── models/
│   ├── __init__.py
│   ├── delegation.py              # V2: Delegation data models
│   ├── agent.py                # Agent data models
│   └── # Removed - replaced by delegation.py
├── services/
│   ├── __init__.py
│   ├── delegation_service.py      # V2: Core delegation service
│   ├── agent_manager.py        # Agent lifecycle
│   ├── opencode_service.py     # OpenCode integration
│   └── # Removed - consolidated into delegation_service.py
├── storage/
│   ├── __init__.py
│   └── database.py             # SQLite persistence
├── utils/
│   ├── __init__.py
│   └── constitution_gate.py    # X^∞ validation
└── handlers/                    # Future: Event handlers
```

## Performance Metrics

Based on 74 passing tests:

| Metric | Value | Target |
|--------|-------|--------|
| Session Creation | <1s | <2s |
| Message Throughput | >5 msg/s | >3 msg/s |
| Max Concurrent Sessions | 5 | 5 |
| Success Rate | 95%+ | 90%+ |
| Memory per Session | ~50MB | <100MB |

## References

- **V2 Migration**: `V2_MIGRATION_TASKS.md` (Complete migration plan)
- **Status Report**: `STATUS_REPORT.md` (Production readiness)
- **Specification**: `/specs/001-agent-orchestrator/spec.md`
- **Planning**: `PLANUNG.md`
- **X^∞ Constitution**: `/home/auctor/CLAUDE.md`
- **Tests**: `tests/test_integration_v2.py` (74/74 passing)

## License

Internal use only - ct_dev project
