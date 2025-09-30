# Phase 0: Research & Technical Decisions

**Feature**: Agent Orchestrator MCP Server  
**Branch**: 001-agent-orchestrator  
**Date**: 2025-01-17

---

## Research Overview

This document consolidates research findings for technical decisions and resolves all NEEDS CLARIFICATION items from the specification. Research focused on: MCP server implementation patterns, opencode serve integration, process management, OpenAPI tooling, and X^∞ ecosystem integration.

---

## Technical Stack Decisions

### 1. Python MCP Server Implementation

**Decision**: Use `mcp` library (v1.13.1) with `fastmcp` (v2.12.3) for rapid MCP server development

**Rationale**:
- Already installed in environment (verified via pip3 list)
- `fastmcp` provides decorators for easy tool registration (`@mcp.tool()`)
- Native Python async/await support for concurrent operations
- Strong typing with Pydantic integration (v2.11.7 available)
- Active development and X^∞ ecosystem compatibility

**Alternatives Considered**:
- Raw `mcp` library only - **rejected**: More boilerplate, slower development
- Custom protocol implementation - **rejected**: Violates KISS principle, high complexity
- TypeScript MCP SDK - **rejected**: Python ecosystem requirement from constitution

**Implementation Approach**:
```python
from fastmcp import FastMCP
from mcp import types

mcp_server = FastMCP("agent-orchestrator")

@mcp_server.tool()
async def create_agent(name: str, capabilities: list[str]) -> dict:
    # Agent creation logic
    pass
```

---

### 2. Opencode Server Management

**Decision**: Use `subprocess` module with `psutil` (v7.0.0) for process lifecycle management

**Rationale**:
- opencode binary installed at `/home/auctor/.opencode/bin/opencode`
- `subprocess.Popen()` provides non-blocking process execution
- `psutil` enables process monitoring (CPU, memory, health checks)
- Native Python stdlib, no additional dependencies
- Aligns with system constraints (no Docker, native Python)

**Opencode Serve Command Structure**:
```bash
opencode serve --hostname <host> --port <port> --openapi <spec_path>
```

**Process Management Pattern**:
```python
import subprocess
import psutil

class OpencodeInstance:
    def __init__(self, hostname: str, port: int):
        self.process = subprocess.Popen([
            "/home/auctor/.opencode/bin/opencode",
            "serve",
            "--hostname", hostname,
            "--port", str(port),
            "--openapi", f"/tmp/agent_{port}_spec.json"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.pid = self.process.pid
        self.psutil_proc = psutil.Process(self.pid)
    
    def health_check(self) -> dict:
        return {
            "alive": self.psutil_proc.is_running(),
            "cpu_percent": self.psutil_proc.cpu_percent(),
            "memory_mb": self.psutil_proc.memory_info().rss / 1024 / 1024
        }
```

**Alternatives Considered**:
- systemd service management - **rejected**: Too heavyweight, reduces flexibility
- Docker containers - **rejected**: Violates constitution (no Docker)
- multiprocessing module - **rejected**: Intended for parallel Python execution, not external processes

---

### 3. OpenAPI 3.1 Specification Generation

**Decision**: Use `openapi-pydantic` (v0.5.1) for spec generation from Pydantic models

**Rationale**:
- Already installed in environment
- Type-safe spec generation from Pydantic models (v2.11.7)
- Native integration with FastAPI/MCP tooling
- Aligns with X^∞ principle: minimize dependencies

**Generation Pattern**:
```python
from openapi_pydantic import OpenAPI, PathItem, Operation
from pydantic import BaseModel

class AgentToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict

def generate_agent_openapi_spec(tools: list[AgentToolSchema]) -> OpenAPI:
    # Generate OpenAPI 3.1 spec from agent tools
    pass
```

**Alternatives Considered**:
- Manual JSON spec writing - **rejected**: Error-prone, violates fail-fast
- FastAPI automatic generation - **rejected**: Not applicable for opencode serve
- Swagger codegen - **rejected**: Additional dependency, over-engineering

---

### 4. State Persistence & Storage

**Decision**: SQLite with Pydantic ORM for agent/task state, JSON files for OpenAPI specs

**Rationale**:
- SQLite: Zero-configuration, file-based, sufficient for orchestrator scale
- No separate database server needed (KISS principle)
- Pydantic models can serialize to/from SQLite (via SQLModel or custom adapter)
- JSON files for OpenAPI specs: Human-readable, git-trackable, opencode-compatible

**Storage Structure**:
```
/home/auctor/dev/ct_dev-agent_orchestrator-mcp/
├── data/
│   ├── orchestrator.db          # SQLite: agents, tasks, delegations
│   └── specs/                   # OpenAPI specs per agent
│       ├── agent_<id>.json
│       └── ...
└── logs/                        # Logfire integration, local debug only
```

**Alternatives Considered**:
- PostgreSQL - **rejected**: Overkill for single-server orchestrator, added complexity
- Redis - **rejected**: In-memory only, persistence concerns
- Pure JSON files - **rejected**: Poor query performance, race conditions

---

### 5. Integration with X^∞ Ecosystem

**Decision**: Direct integration with ct_dev-task-orchestrator (via API/CLI), logfire for logging, Ptah/Serena as global MCP tools

**Rationale**:
- ct_dev-task-orchestrator available at `/home/auctor/srv/ct_dev-task-orchestrator` - use subprocess for CLI or direct Python import if API exists
- logfire v4.3.0 installed - use for centralized logging (not local files per constitution)
- Ptah/Serena: **Global MCP tools available in opencode** - agents can invoke directly, no delegation layer needed
- Simplifies architecture: agents use Ptah/Serena natively via opencode MCP integration

**Integration Pattern**:
```python
import logfire
from mcp import types

logfire.configure(project="agent-orchestrator")

async def delegate_to_task_orchestrator(task_data: dict):
    # Option 1: CLI invocation
    subprocess.run([
        "python3", "/home/auctor/srv/ct_dev-task-orchestrator/cli.py",
        "create", "--data", json.dumps(task_data)
    ])
    
    # Option 2: Direct import (if module structured)
    # from ct_dev.task_orchestrator import api
    # await api.create_task(task_data)

# Ptah/Serena usage by agents (via opencode MCP):
# Agents automatically have access to Ptah/Serena tools
# Example: Agent calls "ptah.search_knowledge" directly in opencode environment
# No orchestrator-side delegation needed - handled by opencode MCP integration
```

**Alternatives Considered**:
- Tight coupling (direct imports) - **rejected**: Violates atomic delegation, creates maintenance burden
- REST API calls - **neutral**: Acceptable if ct_dev-task-orchestrator exposes API, but CLI simpler
- Message queue - **rejected**: Over-engineering, adds infrastructure complexity
- MCP delegation for Ptah/Serena - **rejected**: Unnecessary complexity, they're global in opencode

---

## Edge Case Resolutions

### 1. Server Instance Crash During Agent Execution

**Decision**: Immediate detection → log failure → mark task as `failed` → manual retry after Auctor review

**Rationale**:
- Fail-fast principle: Don't auto-retry without understanding root cause
- Atomic delegation: Return failure to delegator (Auctor) for decision
- State preservation: Task state in SQLite survives process crash
- Health monitoring: psutil detects process death immediately

**Implementation**:
```python
async def monitor_instance_health(instance_id: str):
    instance = get_instance(instance_id)
    if not instance.psutil_proc.is_running():
        logfire.error(f"Instance {instance_id} crashed", 
                      context={"agents": instance.agents, "tasks": instance.tasks})
        mark_tasks_failed(instance.tasks, reason="server_crash")
        notify_delegator(instance.id, "SERVER_CRASH")
        # NO AUTO-RESTART - awaits Auctor clarification
```

**Rejected Alternatives**:
- Automatic retry - **rejected**: Violates fail-fast, may repeat crash
- Task migration to other instance - **rejected**: Complex state transfer, risk of data loss

---

### 2. Conflicting Agent Requests

**Decision**: No automatic conflict resolution - validate uniqueness at creation, queue requests at delegation

**Rationale**:
- Constitution FR-005: Prevent duplicate agents with identical capability sets
- Agent creation validation prevents conflicts before they occur
- Work package delegation: Simple FIFO queue per agent, no priority system (KISS)
- If true resource conflict (e.g., file lock), agent returns deviation to delegator

**Implementation**:
```python
async def create_agent(name: str, capabilities: list[str]) -> dict:
    existing = query_agents(capabilities=capabilities)
    if existing:
        raise ValueError(f"Agent with capabilities {capabilities} already exists: {existing.id}")
    # Proceed with creation

async def delegate_task(agent_id: str, work_package: dict) -> str:
    agent = get_agent(agent_id)
    if agent.status != "idle":
        # Simple queue - agent processes sequentially
        agent.task_queue.append(work_package)
        return "queued"
    return await execute_task(agent, work_package)
```

**Rejected Alternatives**:
- Priority queue - **rejected**: Adds complexity, no requirement for priorities
- Lock manager - **rejected**: Over-engineering, trust agent deviation mechanism

---

### 3. Scaling Limits

**Decision**: Start conservatively: max 10 concurrent agents, max 5 opencode instances

**Rationale**:
- Constitution: Start simple, scale as needed (KISS + YAGNI)
- Resource constraints: Each opencode instance ~200-500MB memory, ~10-20% CPU
- System capacity: Assume 8GB available RAM → 5 instances = 2.5GB max, safe margin
- 10 agents distributed across 5 instances = 2 agents/instance (load balanced)

**Monitoring & Scaling Strategy**:
- Monitor system metrics: `psutil.virtual_memory()`, `psutil.cpu_percent()`
- If memory >75% or CPU >80%: Log warning, block new agent creation
- Scaling decision: Auctor approval required before increasing limits

**Implementation**:
```python
MAX_AGENTS = 10
MAX_INSTANCES = 5

async def create_agent(...):
    if count_active_agents() >= MAX_AGENTS:
        raise ResourceExhaustedError("Max agents reached (10). Scale requires Auctor approval.")
    # Proceed
```

**Future Scaling Path** (not implemented initially):
- Horizontal: Multiple orchestrator instances (requires distributed state)
- Vertical: Increase limits after load testing

---

### 4. Secret Management

**Decision**: Environment variables for API keys, file-based for agent credentials with restricted permissions

**Rationale**:
- Constitution: System is NAT-separated from web, firewall disabled → reduced external threat
- Simple approach: Read from `.env` file (chmod 600) or environment variables
- No rotation initially (KISS) - manual rotation via Auctor when needed
- Audit: logfire logs all credential access (who, when, which agent)

**Implementation**:
```python
import os
from pathlib import Path

SECRETS_FILE = Path("/home/auctor/dev/ct_dev-agent_orchestrator-mcp/data/secrets.env")
SECRETS_FILE.chmod(0o600)  # Read/write for owner only

def load_agent_secret(agent_id: str) -> str:
    # Load from env var or secrets file
    key = f"AGENT_{agent_id}_API_KEY"
    secret = os.getenv(key)
    if not secret:
        with open(SECRETS_FILE) as f:
            for line in f:
                if line.startswith(key):
                    secret = line.split("=")[1].strip()
    logfire.info(f"Secret accessed for agent {agent_id}")
    return secret
```

**Rejected Alternatives**:
- HashiCorp Vault - **rejected**: Over-engineering, external dependency
- Encrypted database - **rejected**: Adds complexity, key management problem shifts
- No secrets - **rejected**: Agents need API keys for external services

---

### 5. Timeout & Escalation

**Decision**: Configurable timeout per work package (default: 5 minutes), automatic escalation on timeout

**Rationale**:
- Fail-fast: Long-running tasks may indicate stuck agent or scope deviation
- Default 5min: Reasonable for most development tasks (code analysis, small implementations)
- Escalation: Don't auto-terminate - return to delegator as scope deviation
- Delegator can extend timeout or investigate issue

**Implementation**:
```python
import asyncio

DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes

async def execute_task_with_timeout(agent: Agent, work_package: WorkPackage):
    try:
        result = await asyncio.wait_for(
            agent.execute(work_package),
            timeout=work_package.timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        )
        return result
    except asyncio.TimeoutError:
        logfire.warning(f"Task {work_package.id} timeout", agent=agent.id)
        return {
            "status": "deviated",
            "reason": "timeout",
            "deviation": f"Task exceeded {work_package.timeout_seconds}s limit",
            "recommendation": "Investigate scope complexity or extend timeout"
        }
```

**Rejected Alternatives**:
- No timeout - **rejected**: Hangs can block agent indefinitely
- Auto-termination - **rejected**: May lose partial results, violates delegation principle
- Adaptive timeout - **rejected**: Complex heuristics, no clear benefit

---

## Performance & Scale Considerations

### Expected Load
- **Concurrent agents**: 10 max initially (5-10 typical)
- **Work package throughput**: ~10-20 tasks/hour (manual orchestration pace)
- **Server instances**: 5 max (2-3 typical)
- **Response time SLA**: <500ms for MCP tool invocations, <5min for task execution

### Resource Allocation
- Per opencode instance: 200-500MB RAM, 10-20% CPU
- Per agent: Negligible (state in DB, logic in opencode)
- Total system: ~3GB RAM, ~60% CPU at peak (5 instances)

### Bottlenecks & Mitigations
- **Bottleneck**: SQLite write contention at high concurrency
  - **Mitigation**: Write-ahead logging (WAL mode), connection pooling
  - **Threshold**: <50 writes/sec (well above expected load)

- **Bottleneck**: opencode serve startup time (~2-5 seconds)
  - **Mitigation**: Pre-start instances on orchestrator boot
  - **Impact**: Negligible for manual orchestration pace

- **Bottleneck**: Network I/O to opencode instances (localhost only)
  - **Mitigation**: None needed - localhost bandwidth >>10Gbps

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| MCP Server | fastmcp | 2.12.3 | Rapid MCP development, decorator-based |
| Process Mgmt | subprocess + psutil | stdlib + 7.0.0 | Opencode instance lifecycle |
| OpenAPI Gen | openapi-pydantic | 0.5.1 | Type-safe spec generation |
| State Store | SQLite | stdlib | Zero-config, sufficient scale |
| Logging | logfire | 4.3.0 | Centralized, constitution-compliant |
| HTTP Client | httpx (if needed) | TBD | Async HTTP for opencode API calls |
| Testing | pytest | TBD | Standard Python testing |
| Language | Python | 3.13.7 | Native environment |

---

## Integration Points

### External Systems
1. **ct_dev-task-orchestrator**: Task tracking and documentation
   - **Interface**: CLI (`subprocess`) or direct import
   - **Location**: `/home/auctor/srv/ct_dev-task-orchestrator`

2. **Ptah (Knowledge Manager)**: Context retrieval
   - **Interface**: Global MCP tool in opencode (agents use directly)
   - **Pattern**: Agents invoke Ptah tools natively via opencode MCP integration
   - **No orchestrator-side delegation needed**

3. **Serena**: Semantic code operations
   - **Interface**: Global MCP tool in opencode (agents use directly)
   - **Pattern**: Agents invoke Serena tools natively via opencode MCP integration
   - **No orchestrator-side delegation needed**

4. **logfire**: Centralized logging
   - **Interface**: Direct Python library
   - **Pattern**: `logfire.info/warn/error(...)`

5. **opencode serve**: Agent runtime
   - **Interface**: HTTP (OpenAPI endpoints)
   - **Pattern**: `httpx.post(f"http://{host}:{port}/api/run", ...)`
   - **MCP Integration**: opencode natively provides Ptah/Serena as global tools

### Internal Components
- Agent Registry (SQLite table)
- Work Package Queue (SQLite + in-memory)
- Server Instance Manager (Python class + psutil)
- MCP Tool Handlers (fastmcp decorators)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| opencode serve instability | Medium | High | Health monitoring, fail-fast, manual restart |
| SQLite corruption | Low | High | WAL mode, regular backups, transaction isolation |
| Resource exhaustion | Low | Medium | Hard limits (10 agents, 5 instances), monitoring |
| Scope creep in agents | Medium | Medium | Atomic delegation enforcement, deviation detection |
| Integration failures | Medium | Medium | Comprehensive contract tests, fail-fast |

---

## Open Questions (Resolved)

All NEEDS CLARIFICATION items from spec have been resolved:

1. ✅ **Retry policy**: No auto-retry, fail-fast with manual review
2. ✅ **Conflict resolution**: Validation at creation, FIFO queue at delegation
3. ✅ **Scaling limits**: 10 agents max, 5 instances max initially
4. ✅ **Secret management**: Env vars + restricted file permissions
5. ✅ **Timeout policy**: 5min default, escalate as deviation (no auto-terminate)

---

## Next Steps

This research document resolves all technical uncertainties. Proceed to:

1. **Phase 1**: Design data model, contracts, and quickstart
2. **Constitution Re-Check**: Validate no over-engineering introduced
3. **Phase 2 Planning**: Describe task generation strategy (without creating tasks)

---

**Research Status**: ✅ COMPLETE  
**All NEEDS CLARIFICATION Resolved**: ✅ YES  
**Ready for Phase 1**: ✅ YES
