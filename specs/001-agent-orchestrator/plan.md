# Implementation Plan: Agent Orchestrator MCP Server

**Branch**: `001-agent-orchestrator` | **Date**: 2025-01-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-agent-orchestrator/spec.md`

---

## Summary

MCP server for orchestrating ct_dev-agents powered by opencode serve instances. Core functionality: agent lifecycle management (create, validate, track), atomic delegation with scope deviation handling, opencode server instance management (start, monitor, failover), and X^∞ ecosystem integration (ct_dev-task-orchestrator, logfire). Agents have native access to Ptah/Serena as global MCP tools in opencode. Technical approach: Python 3.13.7 with fastmcp for MCP server, subprocess+psutil for process management, SQLite for state, OpenAPI specs per agent. Aligns with all 10 X^∞ constitution principles, especially atomic delegation (#IV) and fail-fast (#VIII).

---

## Technical Context

**Language/Version**: Python 3.13.7 (native, no venv per constitution)  
**Primary Dependencies**: fastmcp 2.12.3, mcp 1.13.1, psutil 7.0.0, openapi-pydantic 0.5.1, pydantic 2.11.7, logfire 4.3.0  
**Storage**: SQLite (orchestrator.db for agents/tasks/events) + JSON files (OpenAPI specs per agent in data/specs/)  
**Testing**: pytest (contract tests for MCP tools, integration tests for opencode lifecycle)  
**Target Platform**: Linux (Debian-based host per X^∞ system rules)  
**Project Type**: Single project (MCP server, no frontend)  
**Performance Goals**: <500ms MCP tool response, <5min task execution, 10 concurrent agents, 5 opencode instances  
**Constraints**: No Docker, no venv, Python native, firewall/IP6 disabled (NAT-separated), logfire for logging (not local files)  
**Scale/Scope**: 10 agents max, 5 server instances max, ~10-20 tasks/hour throughput (manual orchestration pace)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Constitution Check (Pre-Research)

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Wirkung vor Maßnahme | ✅ PASS | Spec focuses on effects: orchestration outcomes, delegation integrity, not implementation |
| II. Verantwortung sichtbar machen | ✅ PASS | Delegation events track Cap/Delegation chain, audit trails required (FR-034 to FR-038) |
| III. Schutz der Schwächsten | ✅ PASS | Protection bias monitoring (FR-038), fail-fast prevents cascading failures |
| IV. Atomic Delegation | ✅ PASS | Core requirement: FR-007 to FR-011 enforce atomic work packages, scope deviation handling |
| V. Knowledge Management | ✅ PASS | Ptah available as global MCP tool in opencode (agents use natively) |
| VI. Serena-First Operations | ✅ PASS | Serena available as global MCP tool in opencode (agents use natively) |
| VII. Task Management | ✅ PASS | ct_dev-task-orchestrator integration required (FR-013) for task tracking |
| VIII. Fail Fast and Loud | ✅ PASS | Binary success/failure (FR-031), no auto-retry, manual review on failures |
| IX. No Placeholders/Mocks | ✅ PASS | Input validation before execution (FR-029), only functional code |
| X. KISS & No Over-Engineering | ✅ PASS | Simplest approach: SQLite not PostgreSQL, subprocess not systemd, 10 agents not 100 |

**Gate Result**: ✅ PASS - No violations detected

### Post-Design Constitution Check (After Research)

| Principle | Status | Re-validation |
|-----------|--------|---------------|
| I. Wirkung vor Maßnahme | ✅ PASS | Research decisions effect-focused: fail-fast for crashes, FIFO for simplicity |
| II. Verantwortung sichtbar machen | ✅ PASS | Logfire logs all operations with agent_id, delegator context |
| III. Schutz der Schwächsten | ✅ PASS | Health monitoring protects system from resource exhaustion, hard limits (10/5) |
| IV. Atomic Delegation | ✅ PASS | Deviation returns to delegator, no auto-expansion, queue per agent enforces atomicity |
| V. Knowledge Management | ✅ PASS | Ptah available as global MCP tool (agents use directly in opencode) |
| VI. Serena-First Operations | ✅ PASS | Serena available as global MCP tool (agents use directly in opencode) |
| VII. Task Management | ✅ PASS | subprocess/import integration with ct_dev-task-orchestrator CLI/API |
| VIII. Fail Fast and Loud | ✅ PASS | No auto-retry on crash, timeout escalates as deviation, binary status |
| IX. No Placeholders/Mocks | ✅ PASS | Pydantic validation, database constraints, no mock process managers |
| X. KISS & No Over-Engineering | ✅ PASS | **Validated**: SQLite over PostgreSQL, env vars over Vault, FIFO over priority queue |

**Gate Result**: ✅ PASS - Design maintains constitutional alignment, no complexity creep

---

## Project Structure

### Documentation (this feature)
```
specs/001-agent-orchestrator/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (complete)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── create_agent.yaml
│   ├── delegate_task.yaml
│   ├── query_status.yaml
│   └── manage_server.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
ct_dev-agent_orchestrator-mcp/
├── src/
│   ├── __init__.py
│   ├── models/                  # Pydantic data models
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent, AgentCapability, AgentStatus
│   │   ├── work_package.py      # WorkPackage, WorkPackageStatus, ScopeDeviation
│   │   ├── server_instance.py   # ServerInstance, HealthMetrics
│   │   └── delegation_event.py  # DelegationEvent, ConstitutionGateResult
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── agent_manager.py     # Agent lifecycle (create, validate, track)
│   │   ├── task_delegator.py    # Work package routing and execution
│   │   ├── server_manager.py    # Opencode instance lifecycle (start, monitor, stop)
│   │   └── constitution_checker.py  # Gate validation logic
│   │
│   ├── mcp_tools/               # MCP server tool handlers
│   │   ├── __init__.py
│   │   ├── agent_tools.py       # @mcp.tool() for create_agent, query_agent
│   │   ├── delegation_tools.py  # @mcp.tool() for delegate_task, query_status
│   │   └── server_tools.py      # @mcp.tool() for manage_server, health_check
│   │
│   ├── integrations/            # External system integration
│   │   ├── __init__.py
│   │   ├── task_orchestrator.py # ct_dev-task-orchestrator CLI/API wrapper
│   │   └── opencode_client.py   # HTTP client for opencode serve API
│   │                            # NOTE: Ptah/Serena NOT needed - global MCP tools in opencode
│   │
│   ├── storage/                 # Data persistence
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite connection, schema migration
│   │   ├── agent_repository.py  # Agent CRUD operations
│   │   ├── task_repository.py   # WorkPackage CRUD operations
│   │   └── spec_storage.py      # OpenAPI spec file management
│   │
│   └── server.py                # FastMCP server entry point
│
├── tests/
│   ├── contract/                # Contract tests (MCP tools, OpenAPI schemas)
│   │   ├── test_create_agent_contract.py
│   │   ├── test_delegate_task_contract.py
│   │   ├── test_query_status_contract.py
│   │   └── test_manage_server_contract.py
│   │
│   ├── integration/             # Integration tests (end-to-end scenarios)
│   │   ├── test_agent_lifecycle.py
│   │   ├── test_task_delegation.py
│   │   ├── test_scope_deviation.py
│   │   ├── test_server_failover.py
│   │   └── test_ecosystem_integration.py
│   │
│   └── unit/                    # Unit tests (isolated component logic)
│       ├── test_agent_manager.py
│       ├── test_task_delegator.py
│       ├── test_server_manager.py
│       └── test_constitution_checker.py
│
├── data/                        # Runtime data (gitignored except structure)
│   ├── orchestrator.db          # SQLite database
│   ├── specs/                   # OpenAPI spec JSON files per agent
│   │   └── .gitkeep
│   └── secrets.env              # Agent credentials (chmod 600, gitignored)
│
├── logs/                        # Debug logs only (logfire primary, gitignored)
│   └── .gitkeep
│
├── .gitignore                   # Ignore data/, logs/, *.db, secrets.env
├── pyproject.toml               # Dependencies, project metadata
├── README.md                    # Project documentation
└── AGENTS.md                    # opencode agent-specific context (Phase 1 output)
```

**Structure Decision**: Single project structure selected. This is an MCP server (backend service), not a web app with frontend. Repository root contains src/ for implementation, tests/ for verification, data/ for runtime state, and specs/ for planning documentation. Aligns with constitution's simplicity principle and existing ct_dev component patterns (ct_dev-task-orchestrator in srv/, ct-serena_dev structure).

---

## Phase 0: Outline & Research ✅

**Status**: ✅ COMPLETE (see research.md)

All technical unknowns resolved:
- Python MCP implementation: fastmcp + mcp
- Opencode management: subprocess + psutil
- OpenAPI generation: openapi-pydantic
- Storage strategy: SQLite + JSON files
- Integration approaches: CLI/import, MCP delegation
- Edge case policies: Crash (fail-fast), conflicts (validation), scale (hard limits), secrets (env vars), timeout (escalation)

**Output**: ✅ research.md (17KB, 350+ lines) with complete technical stack and edge case resolutions

---

## Phase 1: Design & Contracts

*Prerequisites: research.md complete ✅*

### 1. Data Model Design → data-model.md

**Entities from Spec** (spec.md Key Entities section):

#### Agent
```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DEACTIVATED = "deactivated"

class Agent(BaseModel):
    id: str = Field(..., description="Unique agent identifier (UUID)")
    name: str = Field(..., min_length=1, max_length=100)
    capabilities: list[str] = Field(..., min_items=1, description="Agent capabilities (e.g., ['code-analyzer', 'python'])")
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    assigned_server_instance_id: str | None = Field(None, description="ID of opencode server instance")
    current_task_id: str | None = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Creator (responsibility tracking)")
    task_queue: list[str] = Field(default_factory=list, description="Queued work package IDs")
    
    # Validation rules from FR-002, FR-005
    # Uniqueness of capabilities enforced at service layer
```

#### WorkPackage
```python
class WorkPackageStatus(str, Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEVIATED = "deviated"

class ScopeDeviation(BaseModel):
    detected_at: datetime
    reason: str
    additional_work_identified: str
    recommendation: str

class WorkPackage(BaseModel):
    id: str = Field(..., description="Unique work package ID (UUID)")
    description: str = Field(..., min_length=1)
    target_effect: str = Field(..., description="What to achieve (effect before action)")
    assigned_agent_id: str | None = None
    status: WorkPackageStatus = Field(default=WorkPackageStatus.SUBMITTED)
    scope_deviation: ScopeDeviation | None = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    delegator: str = Field(..., description="Who delegated (responsibility)")
    timeout_seconds: int = Field(default=300, ge=60, le=3600)
    result: dict | None = None
```

#### ServerInstance
```python
class ServerInstance(BaseModel):
    id: str
    hostname: str = Field(default="localhost")
    port: int = Field(..., ge=1024, le=65535)
    status: str = Field(..., description="running, starting, stopping, failed")
    assigned_agents: list[str] = Field(default_factory=list, description="Agent IDs")
    pid: int | None = Field(None, description="Process ID from subprocess")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    health_metrics: dict = Field(default_factory=dict, description="CPU, memory, uptime from psutil")
    openapi_endpoint: str = Field(..., description="URL to OpenAPI spec, e.g., http://localhost:4096/doc")
```

#### DelegationEvent
```python
class DelegationEvent(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    delegator: str = Field(..., description="Who delegated")
    delegatee_agent_id: str = Field(..., description="Which agent")
    work_package_id: str
    outcome: str = Field(..., description="completed, failed, deviated")
    deviation_reason: str | None = None
    responsibility_chain: str = Field(..., description="Cap → Delegation → Agent path")
```

**State Transitions**:
- Agent: ACTIVE ↔ IDLE ↔ BUSY → ERROR (on failure) → DEACTIVATED (manual)
- WorkPackage: SUBMITTED → ASSIGNED → EXECUTING → {COMPLETED | FAILED | DEVIATED}
- ServerInstance: starting → running → {stopping → stopped | failed}

**Validation Rules**:
- Agent capabilities list must not be empty (FR-002)
- WorkPackage target_effect required (FR-007, FR-030)
- Timeout must be 60-3600 seconds (fail-fast for unreasonable timeouts)
- Responsibility fields (created_by, delegator) required for transparency (FR-034)

**Output**: data-model.md with complete entity definitions, relationships, validation rules, state transitions

---

### 2. API Contracts Generation → /contracts/

**From Functional Requirements**, generate MCP tool contracts:

#### create_agent.yaml (OpenAPI 3.1)
```yaml
openapi: 3.1.0
info:
  title: Create Agent Tool
  version: 1.0.0
paths:
  /tools/create_agent:
    post:
      summary: Create specialized ct_dev-agent
      operationId: create_agent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                  minLength: 1
                  maxLength: 100
                capabilities:
                  type: array
                  items:
                    type: string
                  minItems: 1
                created_by:
                  type: string
                  description: Creator for responsibility tracking
              required: [name, capabilities, created_by]
      responses:
        '200':
          description: Agent created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  agent_id:
                    type: string
                  status:
                    type: string
                    enum: [active, idle]
                  server_instance_endpoint:
                    type: string
        '409':
          description: Duplicate capabilities (FR-005)
        '503':
          description: Max agents reached (10)
```

#### delegate_task.yaml
```yaml
openapi: 3.1.0
info:
  title: Delegate Task Tool
  version: 1.0.0
paths:
  /tools/delegate_task:
    post:
      summary: Delegate atomic work package to agent
      operationId: delegate_task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                agent_id:
                  type: string
                description:
                  type: string
                  minLength: 1
                target_effect:
                  type: string
                  description: What to achieve (effect before action)
                delegator:
                  type: string
                timeout_seconds:
                  type: integer
                  minimum: 60
                  maximum: 3600
                  default: 300
              required: [agent_id, description, target_effect, delegator]
      responses:
        '200':
          description: Task delegated
          content:
            application/json:
              schema:
                type: object
                properties:
                  work_package_id:
                    type: string
                  status:
                    type: string
                    enum: [assigned, queued]
        '404':
          description: Agent not found
```

#### query_status.yaml
```yaml
openapi: 3.1.0
info:
  title: Query Status Tool
  version: 1.0.0
paths:
  /tools/query_status:
    get:
      summary: Get comprehensive orchestrator status
      operationId: query_status
      parameters:
        - name: filter
          in: query
          schema:
            type: string
            enum: [agents, tasks, servers, all]
            default: all
      responses:
        '200':
          description: Status retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  agents:
                    type: array
                    items:
                      type: object
                  running_tasks:
                    type: array
                  server_instances:
                    type: array
                  resource_utilization:
                    type: object
```

#### manage_server.yaml
```yaml
openapi: 3.1.0
info:
  title: Manage Server Tool
  version: 1.0.0
paths:
  /tools/manage_server:
    post:
      summary: Manage opencode server instance lifecycle
      operationId: manage_server
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                action:
                  type: string
                  enum: [start, stop, restart, health_check]
                instance_id:
                  type: string
                  description: Required for stop/restart/health_check
                port:
                  type: integer
                  description: Required for start (auto-assigned if omitted)
              required: [action]
      responses:
        '200':
          description: Action completed
        '503':
          description: Max instances reached (5) for start action
```

**Output**: 4 OpenAPI 3.1 contract files in /contracts/ directory

---

### 3. Contract Tests Generation

**From contracts**, generate failing pytest tests:

```python
# tests/contract/test_create_agent_contract.py
import pytest
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_create_agent_request_schema():
    """Test create_agent accepts valid request per contract"""
    request = {
        "name": "code-analyzer-1",
        "capabilities": ["code-analyzer", "python"],
        "created_by": "auctor"
    }
    # This test MUST FAIL initially (no implementation)
    response = await mcp_client.call_tool("create_agent", request)
    assert response["agent_id"]
    assert response["status"] in ["active", "idle"]

@pytest.mark.asyncio
async def test_create_agent_rejects_duplicate_capabilities():
    """Test FR-005: Prevent duplicate agents"""
    # Create first agent
    await mcp_client.call_tool("create_agent", {
        "name": "agent-1",
        "capabilities": ["code-analyzer"],
        "created_by": "auctor"
    })
    # Second agent with same capabilities MUST return 409
    with pytest.raises(ConflictError):
        await mcp_client.call_tool("create_agent", {
            "name": "agent-2",
            "capabilities": ["code-analyzer"],
            "created_by": "auctor"
        })

@pytest.mark.asyncio
async def test_create_agent_enforces_max_limit():
    """Test scaling limit: max 10 agents"""
    # Create 10 agents
    for i in range(10):
        await mcp_client.call_tool("create_agent", {
            "name": f"agent-{i}",
            "capabilities": [f"capability-{i}"],
            "created_by": "auctor"
        })
    # 11th agent MUST return 503
    with pytest.raises(ResourceExhaustedError):
        await mcp_client.call_tool("create_agent", {
            "name": "agent-11",
            "capabilities": ["extra"],
            "created_by": "auctor"
        })
```

Similar contract tests for delegate_task, query_status, manage_server.

**Output**: Contract test files in tests/contract/ (MUST FAIL before implementation per TDD)

---

### 4. Test Scenarios from User Stories

**From spec.md Acceptance Scenarios**, generate integration tests:

```python
# tests/integration/test_agent_lifecycle.py
@pytest.mark.asyncio
async def test_scenario_1_agent_creation_with_server_instance():
    """
    Scenario 1: Given no agents exist, When architect requests creation 
    of "code-analyzer" agent, Then system creates agent, starts server, 
    registers with MCP, returns ID and endpoint
    """
    # Initial state: no agents
    status = await mcp_client.call_tool("query_status", {"filter": "agents"})
    assert len(status["agents"]) == 0
    
    # Action: create agent
    response = await mcp_client.call_tool("create_agent", {
        "name": "code-analyzer",
        "capabilities": ["code-analyzer", "python"],
        "created_by": "auctor"
    })
    
    # Assertions
    assert response["agent_id"]
    assert response["status"] == "idle"
    assert "server_instance_endpoint" in response
    assert response["server_instance_endpoint"].startswith("http://localhost:")
    
    # Verify server instance started
    servers = await mcp_client.call_tool("query_status", {"filter": "servers"})
    assert len(servers["server_instances"]) == 1
    assert servers["server_instances"][0]["status"] == "running"
```

Additional integration tests for scenarios 2-5 from spec.md.

**Output**: Integration test files in tests/integration/

---

### 5. Quickstart Test Extraction

**From user stories**, create quickstart.md:

```markdown
# Quickstart: Agent Orchestrator MCP Server

## Prerequisites
- Python 3.13.7 installed
- opencode binary at `/home/auctor/.opencode/bin/opencode`
- Dependencies installed: `pip3 install -r requirements.txt`
- SQLite database initialized: `python3 src/storage/database.py migrate`

## Start MCP Server
```bash
python3 src/server.py
# Server starts on stdio (MCP protocol)
```

## Test Scenario: Create Agent and Delegate Task

### 1. Create Code Analyzer Agent
```bash
# Via MCP client (e.g., Claude Desktop)
{
  "tool": "create_agent",
  "arguments": {
    "name": "code-analyzer-1",
    "capabilities": ["code-analyzer", "python"],
    "created_by": "auctor"
  }
}
# Expected: {"agent_id": "...", "status": "idle", "server_instance_endpoint": "http://localhost:XXXX/doc"}
```

### 2. Delegate Analysis Task
```bash
{
  "tool": "delegate_task",
  "arguments": {
    "agent_id": "<from step 1>",
    "description": "Analyze authentication flow in /home/auctor/dev/ct-serena_dev/src/auth.py",
    "target_effect": "Identify security vulnerabilities and best practice violations",
    "delegator": "auctor",
    "timeout_seconds": 300
  }
}
# Expected: {"work_package_id": "...", "status": "executing"}
```

### 3. Query Task Status
```bash
{
  "tool": "query_status",
  "arguments": {
    "filter": "tasks"
  }
}
# Expected: {"running_tasks": [{"id": "...", "status": "executing", "progress": "..."}]}
```

### 4. Handle Scope Deviation (if occurs)
```bash
# If task detects additional work needed, status becomes "deviated"
{
  "status": "deviated",
  "scope_deviation": {
    "reason": "Found additional security issues requiring deeper analysis",
    "recommendation": "Extend timeout or create separate task for cryptographic review"
  }
}
# Auctor reviews, creates new task or extends timeout
```

## Success Criteria
- [ ] Agent created and registered in database
- [ ] Opencode server instance started and healthy
- [ ] Task delegated and executed via opencode API
- [ ] Status queries return accurate real-time data
- [ ] Scope deviation properly captured and returned
- [ ] All operations logged to logfire
```

**Output**: quickstart.md with step-by-step validation scenarios

---

### 6. Update Agent Context File

**Execute agent context update** (O(1) operation):

```bash
# From repository root
.specify/scripts/bash/update-agent-context.sh opencode
# IMPORTANT: No additional arguments per template instructions
```

This script:
- Creates/updates AGENTS.md (for opencode agents)
- Adds NEW tech from this plan (fastmcp, opencode serve, psutil)
- Preserves manual additions between markers
- Updates recent changes (keeps last 3)
- Keeps under 150 lines for token efficiency

**Expected AGENTS.md content** (high-level):
```markdown
# opencode Agent Context: Agent Orchestrator MCP Server

## Project Overview
MCP server for orchestrating ct_dev-agents powered by opencode serve instances.

## Recent Changes
- 2025-01-17: Initial project setup with MCP server, agent lifecycle, opencode management

## Technology Stack
- **MCP Server**: fastmcp 2.12.3 for MCP tool handlers
- **Process Management**: subprocess + psutil 7.0.0 for opencode instance lifecycle
- **Storage**: SQLite for agent/task state, JSON for OpenAPI specs
- **Integration**: ct_dev-task-orchestrator, logfire (Ptah/Serena global in opencode)

## Key Patterns
- Atomic delegation with scope deviation handling
- Fail-fast: no auto-retry, manual review on failures
- Health monitoring: psutil for opencode instance metrics

## Constitution Alignment
- Enforces X^∞ atomic delegation principle (#IV)
- Integrates Ptah (#V) and Serena (#VI) via MCP delegation
- Fail-fast execution (#VIII), no placeholders (#IX)

[Agent-specific context additions here]
```

**Output**: AGENTS.md in repository root (updated via script)

---

**Phase 1 Status**: ✅ DESIGN DOCUMENTED (actual file creation delegated to /tasks)

---

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load base template**: `.specify/templates/tasks-template.md`

2. **Extract from Phase 1 design docs**:
   - **From data-model.md**: Each entity → model creation task [P] (can parallelize)
     - Example: T001 [P] Create Agent model in src/models/agent.py
     - Example: T002 [P] Create WorkPackage model in src/models/work_package.py
   
   - **From contracts/**: Each contract → contract test task [P]
     - Example: T003 [P] Contract test create_agent in tests/contract/test_create_agent_contract.py
     - Example: T004 [P] Contract test delegate_task in tests/contract/test_delegate_task_contract.py
   
   - **From quickstart.md**: Each scenario → integration test
     - Example: T005 Integration test agent creation scenario in tests/integration/test_agent_lifecycle.py

3. **Generate implementation tasks** (to make tests pass):
   - Service layer tasks (AgentManager, TaskDelegator, ServerManager)
   - MCP tool handler tasks (agent_tools.py, delegation_tools.py, server_tools.py)
   - Integration tasks (opencode_client.py, task_orchestrator.py)
   - Infrastructure tasks (database schema, logfire setup)

4. **Apply ordering rules**:
   - **TDD order**: Tests before implementation (contract tests → integration tests → unit tests → implementation)
   - **Dependency order**: Models → Services → Tools → Integration
   - **Mark [P]**: Parallel execution for independent files (models can be created in parallel, contract tests can run in parallel)

5. **Expected task count**: 30-35 numbered, ordered tasks

**Task Categories** (estimated):
- Setup & Infrastructure: 3-4 tasks (database, dependencies, logfire)
- Data Models: 5 tasks [P] (Agent, WorkPackage, ServerInstance, DelegationEvent, ConstitutionGate)
- Contract Tests: 4 tasks [P] (one per MCP tool contract)
- Service Layer: 8-10 tasks (managers, validators, health monitors)
- MCP Tool Handlers: 4 tasks (create_agent, delegate_task, query_status, manage_server)
- Integration Layer: 3-4 tasks (opencode client, ct_dev-task-orchestrator wrapper)
  - **Note**: NO Ptah/Serena integration tasks - they're global in opencode
- Integration Tests: 5 tasks (scenarios from quickstart.md)
- Documentation & Cleanup: 2-3 tasks (README, remove temp files)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan. The /plan command STOPS here.

---

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md with 30-35 numbered tasks)  
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)  
**Phase 5**: Validation (run all tests, execute quickstart.md, performance validation against <500ms, 10 agents, 5 instances goals)

---

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | *No violations detected* | *N/A* |

**Complexity Justification**: All design decisions align with KISS principle:
- SQLite over PostgreSQL: Sufficient for orchestrator scale, zero-config
- Subprocess over systemd/Docker: Simpler process management, no added infrastructure
- FIFO queue over priority queue: No requirement for priorities, reduces complexity
- Env vars over Vault: Adequate for NAT-separated system, no external dependency
- Hard limits (10/5) over auto-scaling: Prevents resource exhaustion, explicit capacity planning

**No over-engineering detected** in Post-Design Constitution Check.

---

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md created
- [x] Phase 1: Design complete (/plan command) ✅ Documented in this plan.md
- [ ] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Documented above
- [ ] Phase 3: Tasks generated (/tasks command) - **NEXT STEP**
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅ (see research.md)
- [x] Complexity deviations documented ✅ (none detected)

---

## Next Steps for /tasks Command

When executing `/tasks`, the system should:

1. Load this plan.md and research.md for context
2. Load data-model.md, contracts/, quickstart.md from Phase 1 (to be created)
3. Generate tasks.md with 30-35 numbered tasks following TDD order
4. Mark [P] for parallel execution where applicable
5. Ensure each task has exact file path and clear acceptance criteria

**Ready for**: ✅ /tasks command execution

---

*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*  
*Planning completed by: Claude (Delegated by Auctor)*  
*Date: 2025-01-17*
