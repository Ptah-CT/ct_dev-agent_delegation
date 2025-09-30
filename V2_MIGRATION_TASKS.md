# Agent Orchestrator V2 Migration - Task Plan

## Overview

Migration von Delegation-basierter zu Session-basierter Architektur gemäß `docs/architecture-v2.md` und `docs/refactoring-plan.md`.

**Ziel**: Interaktive Session-basierte Agent-Kontrolle für PM Agent  
**Timeline**: ~6-8 Stunden  
**Status**: Ready to Start

---

## Task 1: Phase 1 - Session Models

**Title**: Agent Orchestrator V2 Migration: Phase 1 - Session Models

**Priority**: High  
**Complexity**: 5/10  
**Status**: Pending  
**Estimated Time**: 2 hours

**Summary**:
Erstelle neue Session-basierte Models für V2 Architektur. Diese Models ermöglichen Session-basierte Interaktion zwischen PM Agent und Agents.

**Goals**:
- Erstelle `src/ct_dev_agent_orchestrator_mcp/models/session.py`
- Implementiere 4 neue Pydantic Models

**Models to Create**:

1. **SpawnAgentRequest**
   ```python
   class SpawnAgentRequest(BaseModel):
       role: str  # Agent role (e.g., "backend_specialist")
       task_id: str  # Task UUID from task_orchestrator
       instructions: str  # Detailed work instructions
       context: Dict[str, Any] = {}  # Additional context
       model: str = "claude-sonnet-4"  # Model to use
   ```

2. **SessionStatus** (Enum)
   ```python
   class SessionStatus(str, Enum):
       STARTING = "starting"
       RUNNING = "running"
       COMPLETED = "completed"
       FAILED = "failed"
       CANCELLED = "cancelled"
   ```

3. **SessionInfo**
   ```python
   class SessionInfo(BaseModel):
       session_id: str  # UUID
       agent_role: str
       status: SessionStatus
       started_at: str  # ISO 8601
       progress: Dict[str, Any] = {}
       messages: List[Dict] = []
       server_url: str
   ```

4. **AgentOutput**
   ```python
   class AgentOutput(BaseModel):
       session_id: str
       status: SessionStatus
       artifacts: Dict[str, Any] = {}
       summary: str
       duration_seconds: float
       completed_at: str  # ISO 8601
   ```

**Acceptance Criteria**:
- ✓ models/session.py exists with all 4 models
- ✓ Pydantic validation for all fields
- ✓ Type hints complete
- ✓ Tests in tests/test_session_models.py
- ✓ All tests passing

**Files to Create**:
- `src/ct_dev_agent_orchestrator_mcp/models/session.py`
- `tests/test_session_models.py`

**Tags**: `agent-orchestrator`, `v2-migration`, `phase-1`, `models`, `session-based`

---

## Task 2: Phase 2 - SessionService

**Title**: Agent Orchestrator V2 Migration: Phase 2 - SessionService

**Priority**: High  
**Complexity**: 7/10  
**Status**: Pending  
**Estimated Time**: 2 hours  
**Dependencies**: Task 1 (Session Models)

**Summary**:
Implementiere SessionService für Session-basiertes Agent Management. Dies ersetzt die DelegationService Logik mit Session-orientiertem Lifecycle Management.

**Goals**:
- Erstelle `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`
- Implementiere 6 Kern-Methoden

**Methods to Implement**:

1. **spawn_agent**
   ```python
   async def spawn_agent(request: SpawnAgentRequest) -> SessionInfo:
       """
       Spawnt neuen OpenCode Server und erstellt Session.
       Returns session_id für Tracking.
       """
   ```

2. **query_session**
   ```python
   async def query_session(session_id: str) -> SessionInfo:
       """
       Holt aktuellen Status einer Session.
       Nicht-blockierend, returns current state.
       """
   ```

3. **send_to_agent**
   ```python
   async def send_to_agent(session_id: str, message: str) -> bool:
       """
       Sendet Follow-up Message an laufende Session.
       Für Clarifications, Adjustments, etc.
       """
   ```

4. **get_agent_output**
   ```python
   async def get_agent_output(session_id: str) -> AgentOutput:
       """
       Holt finales Output von abgeschlossener Session.
       """
   ```

5. **stop_agent**
   ```python
   async def stop_agent(session_id: str) -> bool:
       """
       Stoppt Session und cleaned up resources.
       """
   ```

6. **list_active_sessions**
   ```python
   async def list_active_sessions() -> List[SessionInfo]:
       """
       Listet alle aktiven Sessions.
       """
   ```

**Integration Points**:
- Nutzt `session_manager.py` für OpenCode API Calls
- Nutzt `opencode_api_client.py` für HTTP Requests
- Nutzt `agent_manager.py` für Process Management
- Lifecycle: spawn → query → send → output → stop

**Acceptance Criteria**:
- ✓ services/session_service.py implemented
- ✓ All 6 methods functional
- ✓ Tests in tests/test_session_service.py
- ✓ Integration with OpenCode API validated
- ✓ Error handling comprehensive
- ✓ All tests passing

**Files to Create**:
- `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`
- `tests/test_session_service.py`

**Tags**: `agent-orchestrator`, `v2-migration`, `phase-2`, `services`, `session-management`

---

## Task 3: Phase 3 - MCP Tools Refactoring

**Title**: Agent Orchestrator V2 Migration: Phase 3 - MCP Tools Refactoring

**Priority**: High  
**Complexity**: 6/10  
**Status**: Pending  
**Estimated Time**: 2 hours  
**Dependencies**: Task 1, Task 2

**Summary**:
Refactoring der MCP Tools in server.py von Delegation-basiert zu Session-basiert. Alte Tools werden umbenannt/ersetzt, neue Tools hinzugefügt.

**Tool Changes**:

| Old Tool | New Tool | Description |
|----------|----------|-------------|
| delegate_work | spawn_agent | Spawnt Agent Session |
| get_delegation_status | query_session | Holt Session Status |
| get_delegation_result | get_agent_output | Holt finales Output |
| list_delegations | list_active_sessions | Listet Sessions |
| cancel_delegation | stop_agent | Stoppt Session |
| - | send_to_agent | NEU: Follow-up Message |
| - | get_agent_capabilities | NEU: Agent Info |

**Implementation Details**:

1. **Update server.py**:
   - Import SessionService statt DelegationService
   - Update @app.list_tools() mit neuen Tool-Namen
   - Update @app.call_tool() Handler
   - User-friendly Response-Texte

2. **Tool Schemas**:
   ```python
   Tool(
       name="spawn_agent",
       description="Spawns a specialized agent session",
       inputSchema={
           "type": "object",
           "properties": {
               "role": {"type": "string"},
               "task_id": {"type": "string"},
               "instructions": {"type": "string"},
               "context": {"type": "object"},
               "model": {"type": "string"}
           }
       }
   )
   ```

3. **Migration Strategy**:
   - Alte Tools als deprecated markieren
   - Parallel betrieb während Test-Phase
   - Nach Validation: Alte Tools entfernen

**Acceptance Criteria**:
- ✓ All 7 tools in server.py updated
- ✓ Tests in tests/test_mcp_tools_v2.py
- ✓ Old tools deprecated (or removed)
- ✓ Documentation updated
- ✓ User-friendly responses
- ✓ All tests passing

**Files to Modify**:
- `src/ct_dev_agent_orchestrator_mcp/server.py`

**Files to Create**:
- `tests/test_mcp_tools_v2.py`

**Tags**: `agent-orchestrator`, `v2-migration`, `phase-3`, `mcp-tools`, `server`

---

## Task 4: Phase 4 - Integration Tests

**Title**: Agent Orchestrator V2 Migration: Phase 4 - Integration Tests

**Priority**: Medium  
**Complexity**: 7/10  
**Status**: Pending  
**Estimated Time**: 2 hours  
**Dependencies**: Task 1, 2, 3

**Summary**:
Erstelle umfassende Integration Tests für die V2 Session-basierte Architektur. Tests validieren den vollständigen Flow von PM Agent → SessionService → OpenCode → Agent.

**Test Files to Create**:

### 1. `tests/integration/test_spawn_flow.py`

**Tests**:
- ✓ test_spawn_agent_creates_opencode_session
- ✓ test_spawn_agent_returns_session_id
- ✓ test_spawn_agent_health_checks
- ✓ test_spawn_agent_with_different_roles
- ✓ test_spawn_agent_error_handling

### 2. `tests/integration/test_session_lifecycle.py`

**Tests**:
- ✓ test_full_session_lifecycle
  - spawn → query → send → output → stop
- ✓ test_session_status_transitions
- ✓ test_session_cleanup_on_stop
- ✓ test_session_error_recovery
- ✓ test_multiple_sessions_parallel

### 3. `tests/integration/test_pm_agent_interaction.py`

**Tests**:
- ✓ test_pm_agent_spawns_backend_specialist
- ✓ test_pm_agent_polls_session_status
- ✓ test_pm_agent_sends_followup
- ✓ test_pm_agent_gets_final_output
- ✓ test_pm_agent_handles_agent_failure

**Mock Strategy**:
```python
# Mock OpenCode Server Responses
@pytest.fixture
def mock_opencode_server():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://localhost:8000/session", 
                 json={"id": "session-123"}, status=200)
        rsps.add(responses.GET, "http://localhost:8000/health",
                 json={"status": "healthy"}, status=200)
        yield rsps
```

**Acceptance Criteria**:
- ✓ 3 test files created
- ✓ Minimum 15 integration tests
- ✓ Mock OpenCode Server functional
- ✓ All test scenarios covered
- ✓ Test coverage > 80%
- ✓ All tests passing

**Files to Create**:
- `tests/integration/test_spawn_flow.py`
- `tests/integration/test_session_lifecycle.py`
- `tests/integration/test_pm_agent_interaction.py`
- `tests/integration/__init__.py`

**Tags**: `agent-orchestrator`, `v2-migration`, `phase-4`, `integration-tests`, `testing`

---

## Task 5: Phase 5 - Documentation & Cleanup

**Title**: Agent Orchestrator V2 Migration: Phase 5 - Documentation & Cleanup

**Priority**: Medium  
**Complexity**: 4/10  
**Status**: Pending  
**Estimated Time**: 1-2 hours  
**Dependencies**: Task 1, 2, 3, 4

**Summary**:
Finalisiere V2 Migration mit Dokumentations-Updates, Code Cleanup und Version Tagging. Stelle sicher dass alle Dokumentation die neue Architektur reflektiert.

**Documentation Updates**:

1. **README.md**
   - Update MCP Tools section mit neuen Tool-Namen
   - Add V2 Architecture diagram
   - Update usage examples
   - Add migration notes

2. **CHANGELOG.md**
   - Add Version 0.2.0 entry
   - List all V2 changes
   - Migration guide for users

3. **docs/architecture-v2.md**
   - Mark as "current" architecture
   - Add implementation details
   - Add performance notes

4. **API Examples**
   ```markdown
   ## V2 API Examples
   
   ### Spawn Agent
   ```json
   {
     "role": "backend_specialist",
     "task_id": "550e8400-...",
     "instructions": "Implement OAuth2 endpoints"
   }
   ```
   
   Response:
   ```json
   {
     "session_id": "abc-123",
     "status": "starting",
     "server_url": "http://localhost:8001"
   }
   ```
   ```

**Code Cleanup**:

1. **Deprecate/Remove Old Code**:
   - ✓ models/delegation.py → deprecate or remove
   - ✓ services/delegation_service.py → deprecate or remove
   - ✓ Old MCP tools in server.py → remove

2. **Clean Imports**:
   - ✓ Remove unused imports
   - ✓ Update __init__.py files
   - ✓ Fix any circular imports

3. **Code Comments**:
   - ✓ Update comments to reflect V2
   - ✓ Add docstrings where missing
   - ✓ Update type hints

**Final Validation**:
```bash
# Run all tests
pytest -v

# Check code style
pylint src/

# Start server
./RUN_SERVER.sh

# Verify Logfire
# Check Dashboard for logs
```

**Acceptance Criteria**:
- ✓ All documentation updated for V2
- ✓ Old code removed or deprecated
- ✓ Tests 100% passing (Unit + Integration)
- ✓ Server starts without errors
- ✓ Logfire monitoring functional
- ✓ Version 0.2.0 tagged in git

**Files to Update**:
- README.md
- CHANGELOG.md
- docs/architecture-v2.md
- src/ct_dev_agent_orchestrator_mcp/__init__.py

**Files to Remove/Deprecate**:
- models/delegation.py (optional)
- services/delegation_service.py (optional)

**Git Commands**:
```bash
git add -A
git commit -m "feat: Complete V2 Migration to Session-based Architecture

- Session Models implemented
- SessionService for lifecycle management
- MCP Tools refactored to Session-based
- Integration tests comprehensive
- Documentation updated
- Old code cleaned up

Version 0.2.0 - Session-based Architecture"

git tag -a v0.2.0 -m "Version 0.2.0: Session-based Architecture"
```

**Tags**: `agent-orchestrator`, `v2-migration`, `phase-5`, `documentation`, `cleanup`

---

## Migration Summary

### Total Effort Estimate
- **Phase 1**: 2 hours (Models)
- **Phase 2**: 2 hours (SessionService)
- **Phase 3**: 2 hours (MCP Tools)
- **Phase 4**: 2 hours (Integration Tests)
- **Phase 5**: 1-2 hours (Docs & Cleanup)

**Total**: 9-10 hours

### Success Criteria
- ✓ All 5 phases completed
- ✓ All tests passing (Unit + Integration)
- ✓ Server functional with V2 tools
- ✓ Documentation complete and accurate
- ✓ Version 0.2.0 tagged

### Key Benefits of V2
1. **Interactive Control**: PM Agent can communicate during execution
2. **Progress Tracking**: Real-time status via query_session
3. **Flexibility**: Follow-up messages via send_to_agent
4. **OpenCode Integration**: Full OpenCode API utilization
5. **Better UX**: Clearer, more intuitive API for PM Agent

### Risk Mitigation
- Parallel operation during migration (old + new tools)
- Comprehensive testing before old code removal
- Documentation for migration path
- Rollback plan if issues arise

---

**Status**: Ready to Start  
**Next**: Begin Phase 1 (Session Models)  
**Reference**: See `docs/refactoring-plan.md` for detailed implementation guide
