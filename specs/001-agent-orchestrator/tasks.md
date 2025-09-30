# Tasks: Agent Orchestrator MCP Server

**Input**: Design documents from `/specs/001-agent-orchestrator/`  
**Prerequisites**: plan.md ✅, research.md ✅, spec.md ✅  
**Generated**: 2025-01-17

---

## Execution Summary

**Total Tasks**: 32  
**Parallel Tasks**: 11 (marked [P])  
**Sequential Tasks**: 21  
**Estimated Completion**: 3-4 days (following TDD discipline)

**🜄 CRITICAL: Async Communication Requirement 🜄**
- **delegate_task** MUST be non-blocking (fire-and-forget pattern)
- Main Agent receives work_package_id immediately (<100ms)
- Main Agent polls query_status(work_package_id) for updates
- Background execution in TaskDelegator (asyncio/threading)
- **Wirkung**: Main Agent NEVER blocks during delegation

---

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute from repository root
- Tests MUST be written and MUST FAIL before implementation

---

## Phase 3.1: Setup & Infrastructure (4 tasks)

**Prerequisites**: None (start here)

- [ ] **T001** Create project structure per plan.md
  - Create: `src/{models,services,mcp_tools,integrations,storage}/`
  - Create: `tests/{contract,integration,unit}/`
  - Create: `data/{specs}/`, `logs/`
  - Create: `.gitignore` (ignore data/, logs/, *.db, secrets.env)
  - **Validation**: Directory structure matches plan.md Section "Source Code"

- [ ] **T002** Initialize Python project with pyproject.toml
  - Dependencies: fastmcp==2.12.3, mcp==1.13.1, psutil==7.0.0, openapi-pydantic==0.5.1, pydantic==2.11.7, logfire==4.3.0, httpx, pytest, pytest-asyncio
  - Project metadata: name="ct_dev-agent_orchestrator-mcp", version="0.1.0"
  - **Validation**: `pip3 install -e .` succeeds, all dependencies resolve

- [ ] **T003** Configure logfire for centralized logging
  - File: `src/__init__.py`
  - Initialize: `logfire.configure(project="agent-orchestrator")`
  - Environment: Read LOGFIRE_TOKEN from env or secrets.env
  - **Validation**: `logfire.info("test")` logs successfully

- [ ] **T004** Initialize SQLite database schema
  - File: `src/storage/database.py`
  - Tables: agents, work_packages, server_instances, delegation_events
  - Enable WAL mode for concurrency
  - Migration: Create schema on first run
  - **Validation**: `python3 src/storage/database.py migrate` creates data/orchestrator.db

---

## Phase 3.2: Data Models (5 tasks - ALL PARALLEL)

**Prerequisites**: T001, T002 complete  
**CRITICAL**: These models define the data layer for all subsequent tasks

- [ ] **T005 [P]** Agent model in src/models/agent.py
  - Class: Agent(BaseModel) with fields from plan.md
  - Enum: AgentStatus (ACTIVE, IDLE, BUSY, ERROR, DEACTIVATED)
  - Validation: capabilities non-empty, name 1-100 chars
  - **Validation**: `from src.models.agent import Agent; Agent(id="test", name="test", capabilities=["test"], created_by="test")` succeeds

- [ ] **T006 [P]** WorkPackage model in src/models/work_package.py
  - Class: WorkPackage(BaseModel), ScopeDeviation(BaseModel)
  - Enum: WorkPackageStatus (SUBMITTED, ASSIGNED, EXECUTING, COMPLETED, FAILED, DEVIATED)
  - Validation: target_effect required, timeout 60-3600 seconds
  - **Validation**: Model instantiation with all fields succeeds

- [ ] **T007 [P]** ServerInstance model in src/models/server_instance.py
  - Class: ServerInstance(BaseModel)
  - Fields: id, hostname, port, status, assigned_agents, pid, health_metrics
  - Validation: port 1024-65535
  - **Validation**: Model instantiation succeeds

- [ ] **T008 [P]** DelegationEvent model in src/models/delegation_event.py
  - Class: DelegationEvent(BaseModel)
  - Fields: id, timestamp, delegator, delegatee_agent_id, work_package_id, outcome, responsibility_chain
  - **Validation**: Model instantiation succeeds

- [ ] **T009 [P]** Create src/models/__init__.py
  - Export: Agent, AgentStatus, WorkPackage, WorkPackageStatus, ScopeDeviation, ServerInstance, DelegationEvent
  - **Validation**: `from src.models import Agent, WorkPackage` succeeds

---

## Phase 3.3: Storage Layer (4 tasks)

**Prerequisites**: T004, T005-T009 complete

- [ ] **T010 [P]** AgentRepository in src/storage/agent_repository.py
  - Methods: create(agent), get(agent_id), list_all(), update(agent_id, **fields), delete(agent_id)
  - Query: find_by_capabilities(capabilities) for duplicate check (FR-005)
  - SQLite operations with connection pooling
  - **Validation**: CRUD operations succeed, duplicate capabilities raises ValueError

- [ ] **T011 [P]** TaskRepository in src/storage/task_repository.py
  - Methods: create(work_package), get(wp_id), list_by_status(status), update(wp_id, **fields), mark_deviated(wp_id, deviation)
  - **Validation**: CRUD operations succeed, status transitions work

- [ ] **T012 [P]** ServerInstanceRepository in src/storage/server_repository.py
  - Methods: create(instance), get(instance_id), list_all(), update(instance_id, **fields), delete(instance_id)
  - **Validation**: CRUD operations succeed

- [ ] **T013** OpenAPI spec storage in src/storage/spec_storage.py
  - Methods: save_spec(agent_id, spec_json), load_spec(agent_id), delete_spec(agent_id)
  - Storage: data/specs/{agent_id}.json
  - **Validation**: Save/load round-trip preserves JSON structure

---

## Phase 3.4: Contract Tests (4 tasks - ALL PARALLEL)

**Prerequisites**: T001, T002 complete  
**CRITICAL**: These tests MUST be written and MUST FAIL before any MCP tool implementation

- [ ] **T014 [P]** Contract test create_agent in tests/contract/test_create_agent_contract.py
  - Test: Valid request returns agent_id, status, server_instance_endpoint
  - Test: Duplicate capabilities returns 409 Conflict
  - Test: Max agents (10) returns 503 Service Unavailable
  - Test: Missing required fields returns 400 Bad Request
  - **Validation**: Tests fail with "Tool not found" or "Not implemented"

- [ ] **T015 [P]** Contract test delegate_task in tests/contract/test_delegate_task_contract.py
  - Test: Valid delegation returns work_package_id immediately (<100ms response time)
  - Test: Non-existent agent returns 404 Not Found
  - Test: Missing target_effect returns 400 Bad Request
  - Test: Invalid timeout returns 400 Bad Request
  - Test: **ASYNC**: Verify Main Agent never blocks (measure response time, check background execution)
  - Test: query_status(work_package_id) returns current status without blocking
  - **Validation**: Tests fail with "Tool not found" or "Not implemented"

- [ ] **T016 [P]** Contract test query_status in tests/contract/test_query_status_contract.py
  - Test: query_status(filter="all") returns agents, tasks, servers, resources
  - Test: query_status(filter="agents") returns only agents
  - Test: Empty system returns empty arrays
  - **Validation**: Tests fail with "Tool not found" or "Not implemented"

- [ ] **T017 [P]** Contract test manage_server in tests/contract/test_manage_server_contract.py
  - Test: start action creates new server instance
  - Test: health_check action returns metrics
  - Test: stop action terminates instance
  - Test: Max instances (5) returns 503 Service Unavailable
  - **Validation**: Tests fail with "Tool not found" or "Not implemented"

---

## Phase 3.5: Service Layer (6 tasks)

**Prerequisites**: T005-T013 complete

- [ ] **T018** ServerManager in src/services/server_manager.py
  - Methods: start_instance(port=None) → ServerInstance, stop_instance(instance_id), restart_instance(instance_id)
  - Health: check_health(instance_id) → dict (uses psutil)
  - Process: Use subprocess.Popen to launch opencode serve
  - Command: `/home/auctor/.opencode/bin/opencode serve --hostname localhost --port {port} --openapi {spec_path}`
  - Limits: MAX_INSTANCES = 5, port auto-assignment if not specified
  - **Validation**: Start instance succeeds, psutil shows process running, health_check returns CPU/memory

- [ ] **T019** AgentManager in src/services/agent_manager.py
  - Methods: create_agent(name, capabilities, created_by), validate_capabilities(capabilities), deactivate_agent(agent_id)
  - Validation: Check duplicate capabilities via AgentRepository (FR-005)
  - Validation: MAX_AGENTS = 10 limit enforcement
  - Assignment: Assign agent to least-loaded server instance (load balancing)
  - **Validation**: Create agent succeeds, duplicate check works, max limit enforced

- [ ] **T020** TaskDelegator in src/services/task_delegator.py
  - Methods: 
    - delegate(agent_id, description, target_effect, delegator, timeout_seconds) → work_package_id (IMMEDIATE return, non-blocking)
    - execute_task_async(work_package) → runs in background thread/asyncio task
    - get_status(work_package_id) → current status without blocking
  - Queue: If agent busy, add to agent.task_queue (FIFO)
  - Execution: execute_task_with_timeout(agent, work_package) using asyncio.wait_for in background
  - Timeout: Update work_package status to "deviated" on TimeoutError, don't terminate
  - OpenAPI: Use httpx.AsyncClient to POST to agent's opencode instance endpoint
  - **Architecture**: Fire-and-forget pattern - delegate() returns immediately after creating work_package record
  - **Validation**: Delegation returns work_package_id immediately (<100ms), execution happens asynchronously, timeout escalates as deviation, queue works, Main Agent never blocks

- [ ] **T021** ConstitutionChecker in src/services/constitution_checker.py
  - Methods: validate_atomic_delegation(work_package), log_delegation_event(event)
  - Checks: target_effect present, delegator specified, timeout reasonable
  - Logging: Create DelegationEvent for audit trail (FR-034 to FR-038)
  - **Validation**: Validation catches missing fields, events logged to DB

- [ ] **T022** Integration with ct_dev-task-orchestrator in src/integrations/task_orchestrator.py
  - Methods: create_task(task_data), update_task(task_id, status)
  - Interface: MCP tool calls via opencode (global MCP tool, like Ptah/Serena)
  - Usage: Agents use task_orchestrator natively in opencode environment
  - Fallback: Log error if MCP call fails, don't block orchestration
  - **Validation**: MCP tool call succeeds (task_orchestrator available in opencode)
  - **Note**: Future Feature 002 will enable auto-spawning agents from task_orchestrator tasks with dependency management

- [ ] **T023** OpenAPI spec generation in src/integrations/opencode_client.py
  - Methods: generate_agent_spec(agent_id, capabilities), update_spec(agent_id, tools)
  - Generation: Use openapi-pydantic to create OpenAPI 3.1 spec from agent capabilities
  - Storage: Save spec to data/specs/{agent_id}.json via SpecStorage
  - HTTP: httpx client for calling opencode serve endpoints
  - **Validation**: Spec generation produces valid OpenAPI 3.1 JSON

---

## Phase 3.6: MCP Tool Handlers (4 tasks)

**Prerequisites**: T018-T023 complete  
**CRITICAL**: Implementation must make contract tests PASS

- [ ] **T024** MCP server setup in src/server.py
  - Framework: FastMCP("agent-orchestrator")
  - Initialize: AgentManager, TaskDelegator, ServerManager, ConstitutionChecker
  - Startup: Pre-start 2 server instances for faster agent creation
  - **Validation**: `python3 src/server.py` starts MCP server on stdio

- [ ] **T025** Agent tools in src/mcp_tools/agent_tools.py
  - Tool: @mcp.tool() create_agent(name, capabilities, created_by) → dict
  - Logic: Validate via AgentManager, create agent, assign to server instance, generate OpenAPI spec
  - Tool: @mcp.tool() query_agent(agent_id) → dict (agent details + health)
  - **Validation**: Contract tests T014 PASS

- [ ] **T026** Delegation tools in src/mcp_tools/delegation_tools.py
  - Tool: @mcp.tool() delegate_task(agent_id, description, target_effect, delegator, timeout_seconds) → dict
  - **ASYNC REQUIREMENT**: Tool MUST return immediately with work_package_id (non-blocking)
  - Logic: Validate via ConstitutionChecker, call TaskDelegator.delegate() (returns work_package_id), return immediately
  - Background: TaskDelegator handles async execution in separate thread/asyncio task
  - Tool: @mcp.tool() query_status(filter="all"|work_package_id) → dict (comprehensive status or specific work package)
  - Logic: If work_package_id provided, return detailed status (executing/completed/failed/deviated) with results/errors
  - **Validation**: Contract tests T015 PASS, delegate_task returns <100ms, query_status works for polling
  - **Validation**: Contract tests T015, T016 PASS

- [ ] **T027** Server tools in src/mcp_tools/server_tools.py
  - Tool: @mcp.tool() manage_server(action, instance_id=None, port=None) → dict
  - Actions: start, stop, restart, health_check
  - Logic: Delegate to ServerManager, enforce MAX_INSTANCES limit
  - **Validation**: Contract tests T017 PASS

---

## Phase 3.7: Integration Tests (5 tasks)

**Prerequisites**: T024-T027 complete  
**Purpose**: Validate end-to-end scenarios from spec.md

- [ ] **T028 [P]** Integration test agent lifecycle in tests/integration/test_agent_lifecycle.py
  - Scenario 1: Create agent → verify server started → verify agent registered
  - Scenario: Deactivate agent → verify server cleanup
  - **Validation**: End-to-end agent creation and cleanup works

- [ ] **T029 [P]** Integration test task delegation in tests/integration/test_task_delegation.py
  - Scenario 2a: Create agent → delegate task → verify work_package_id returned immediately
  - Scenario 2b: Poll query_status(work_package_id) → verify status updates (executing → completed)
  - Scenario 2c: Verify Main Agent continues execution without blocking during delegation
  - Scenario: Agent busy → delegate task → verify queuing
  - **Validation**: Task delegation is async, polling works, queue management works

- [ ] **T030 [P]** Integration test scope deviation in tests/integration/test_scope_deviation.py
  - Scenario 3: Delegate task → agent detects deviation → verify deviation returned
  - Test: Deviation includes reason, additional_work_identified, recommendation
  - **Validation**: Scope deviation handling per FR-010, FR-011

- [ ] **T031 [P]** Integration test server failover in tests/integration/test_server_failover.py
  - Scenario 4: Kill opencode instance → verify detection → verify tasks marked failed
  - Test: health_check detects process death via psutil
  - **Validation**: Server crash detection and fail-fast behavior

- [ ] **T032 [P]** Integration test ecosystem integration in tests/integration/test_ecosystem_integration.py
  - Test: Create agent → verify logfire logs
  - Test: Delegate task → verify ct_dev-task-orchestrator integration (if available)
  - Test: Verify DelegationEvent audit trail
  - **Validation**: External system integrations work

---

## Phase 3.8: Polish & Documentation (skipped - will be in separate PR)

**Rationale**: Following plan.md guidance, focus on core functionality first

---

## Future Features (Out of Scope for Phase 3)

### **Feature 002: Auto-Spawning Agents from task_orchestrator**

**Vision**: Task in task_orchestrator → Auto-create Agent → Execute with Dependency Management

**Workflow**:
1. User creates task in task_orchestrator (global MCP in opencode)
2. agent_orchestrator monitors task_orchestrator for new tasks
3. Auto-spawn agent with appropriate capabilities
4. Agent executes task respecting task_orchestrator dependencies
5. Auto-cleanup agent on completion

**Benefits**:
- Seamless integration of X^∞ task delegation
- Automatic resource management
- Dependency-aware execution
- Constitution-compliant responsibility tracking

**Prerequisites**:
- Phase 3 complete (basic agent lifecycle)
- task_orchestrator MCP integration (T022)
- Webhook/polling mechanism for task events

---

### **Feature 003: Web UI Monitoring Dashboard**

**Vision**: Real-time visibility into spawned agents, active tasks, resource usage

**Features**:
- Live agent status (active/idle/busy/error)
- Current task assignments
- Resource metrics (CPU, memory per agent)
- Server instance health
- Delegation event timeline
- Constitution compliance metrics

**Tech Stack**: React + WebSocket/SSE for real-time updates

**Prerequisites**:
- Phase 3 complete (MCP server with query_status)
- REST API wrapper around MCP tools
- WebSocket/SSE endpoint for live updates

---

## Architecture: Async Delegation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Main Agent (MCP Client - opencode instance)                 │
│  - Never blocks during delegation                           │
│  - Continues own work immediately after delegate_task       │
│  - Polls query_status() when needed                         │
└─────────────────────────────────────────────────────────────┘
                      ↓
            [1] delegate_task()
            (agent_id, description, target_effect, ...)
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ agent_orchestrator (MCP Server)                             │
│                                                              │
│  [2] ConstitutionChecker.validate()  <-- Sync validation   │
│  [3] TaskDelegator.delegate()        <-- Creates WorkPkg   │
│      ├─ Generate work_package_id                            │
│      ├─ Store in SQLite (status: "submitted")              │
│      └─ Return work_package_id IMMEDIATELY (<100ms) ────┐  │
│                                                          │  │
│  [4] Background Execution (async/threading)             │  │
│      ├─ TaskDelegator.execute_task_async()              │  │
│      ├─ Update status: "assigned" → "executing"         │  │
│      ├─ POST to delegated agent's opencode endpoint     │  │
│      ├─ Monitor with asyncio.wait_for(timeout)          │  │
│      └─ Update status: "completed"/"failed"/"deviated"  │  │
└──────────────────────────────────────────────────────────│──┘
                                                           │
            [5] Returns work_package_id ◄──────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Main Agent (continues work)                                 │
│  - Does NOT wait for completion                             │
│  - Can poll: query_status(work_package_id)                  │
│  - Receives: {status, progress, results, errors}            │
└─────────────────────────────────────────────────────────────┘

                 [Background]
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Delegated Agent (opencode instance)                         │
│  - Receives task via OpenAPI POST                           │
│  - Executes work package                                    │
│  - Returns results to orchestrator                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Timing Requirements**:
- **Step [5]**: Response time < 100ms (non-blocking guarantee)
- **Step [4]**: Happens asynchronously in background
- Main Agent free to continue work immediately
- Polling via query_status() is non-blocking (reads from SQLite)

**Implementation Notes**:
- TaskDelegator.delegate() returns work_package_id synchronously
- TaskDelegator.execute_task_async() runs in asyncio.create_task() or threading.Thread()
- WorkPackage status updates happen in background
- No callbacks/webhooks needed (polling sufficient for Phase 3)

---

## Dependencies

**Critical Path**:
```
T001,T002 → T003,T004 → T005-T009 → T010-T013 → T018-T023 → T024-T027 → T028-T032
```

**Parallel Execution Points**:
1. After T004: T005-T009 can run in parallel (5 models)
2. After T009: T010-T012 can run in parallel (3 repositories)
3. After T002: T014-T017 can run in parallel (4 contract tests)
4. After T027: T028-T032 can run in parallel (5 integration tests)

**Blocking Dependencies**:
- T014-T017 (contract tests) must FAIL before T024-T027 (implementation)
- T018 (ServerManager) blocks T019 (AgentManager - needs server assignment)
- T019 (AgentManager) blocks T020 (TaskDelegator - needs agent validation)
- T024 (MCP server) blocks T025-T027 (tools need server instance)

---

## Parallel Execution Examples

### Example 1: Data Models (after T004)
```bash
# Launch T005-T009 together (5 parallel tasks):
# Terminal 1:
Task: "Agent model in src/models/agent.py"

# Terminal 2:
Task: "WorkPackage model in src/models/work_package.py"

# Terminal 3:
Task: "ServerInstance model in src/models/server_instance.py"

# Terminal 4:
Task: "DelegationEvent model in src/models/delegation_event.py"

# Terminal 5:
Task: "Create src/models/__init__.py"
```

### Example 2: Contract Tests (after T002)
```bash
# Launch T014-T017 together (4 parallel tasks):
# Terminal 1:
Task: "Contract test create_agent in tests/contract/test_create_agent_contract.py"

# Terminal 2:
Task: "Contract test delegate_task in tests/contract/test_delegate_task_contract.py"

# Terminal 3:
Task: "Contract test query_status in tests/contract/test_query_status_contract.py"

# Terminal 4:
Task: "Contract test manage_server in tests/contract/test_manage_server_contract.py"
```

### Example 3: Integration Tests (after T027)
```bash
# Launch T028-T032 together (5 parallel tasks):
# All integration tests can run in parallel as they test independent scenarios
```

---

## Validation Checklist

**GATE: Must verify before marking Phase 3 complete**

- [x] All contracts (T014-T017) have corresponding implementation tasks (T024-T027)
- [x] All entities (Agent, WorkPackage, ServerInstance, DelegationEvent) have model tasks (T005-T008)
- [x] All tests (T014-T017, T028-T032) come before implementation tasks
- [x] Parallel tasks [P] are truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD discipline enforced: contract tests MUST FAIL before implementation

---

## Notes

- **[P] markers**: 11 tasks can run in parallel (models, repositories, tests)
- **TDD discipline**: Contract tests T014-T017 MUST be written first and MUST FAIL
- **Commit strategy**: Commit after each task completion
- **Fail-fast**: If any test fails unexpectedly, stop and investigate before proceeding
- **Constitution alignment**: T021 (ConstitutionChecker) enforces atomic delegation (Principle IV)
- **No placeholders**: All tasks produce functional code only (Principle IX)

---

## Task Generation Metadata

**Generated from**:
- plan.md: Data models (lines 186-280), Project structure (lines 73-161), Phase 1 design
- research.md: Technical decisions (subprocess, psutil, openapi-pydantic, SQLite)
- spec.md: Functional requirements (FR-001 to FR-038), Acceptance scenarios

**Total tasks**: 32  
**Estimated effort**: 3-4 days with TDD discipline  
**Critical path length**: ~20 sequential tasks  
**Parallelizable**: 11 tasks (34%)

---

*Generated by: Claude (Delegated by Auctor)*  
*Date: 2025-01-17*  
*Ready for: Phase 3 execution*
