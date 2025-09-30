# Refactoring Plan: Delegation → Session Model

## 🎯 Ziel
Umbau von Delegation-basiertem zu Session-basiertem Agent Management gemäß Architecture V2.

## 📋 Änderungen

### 1. MCP Tools Umbenennung und Anpassung

#### Zu ändern in server.py:
```python
# ALT                          # NEU
delegate_work         →        spawn_agent
get_delegation_status →        query_session  
get_delegation_result →        get_agent_output
list_delegations      →        list_active_sessions
cancel_delegation     →        stop_agent

# NEU hinzufügen:
send_to_agent         →        (neu)
get_agent_capabilities →       (neu)
```

### 2. Service Layer Refactoring

#### delegation_service.py → session_service.py
- Rename Class: `DelegationService` → `SessionService`
- Fokus auf Session Lifecycle statt Work Execution
- Nutzt `session_manager.py` für OpenCode API Calls

#### session_manager.py (bereits vorhanden)
- Erweitern um:
  - `send_message_to_session(session_id, message)`
  - `get_session_history(session_id)`
  - `get_session_artifacts(session_id)`

### 3. Model Anpassungen

#### delegation.py → session.py
```python
# ALT
class DelegationRequest
class DelegationResponse  
class DelegationResult

# NEU
class SpawnAgentRequest
class SessionInfo
class AgentOutput
```

### 4. OpenCode API Client Erweiterung

#### opencode_api_client.py ergänzen:
```python
async def get_session_history(server_url: str, session_id: str)
async def send_session_message(server_url: str, session_id: str, message: str)
async def get_session_artifacts(server_url: str, session_id: str)
async def delete_session(server_url: str, session_id: str)
```

## 🔨 Implementierungsschritte

### Step 1: Neue Models erstellen
- [ ] `src/ct_dev_agent_orchestrator_mcp/models/session.py`
- [ ] SpawnAgentRequest, SessionInfo, AgentOutput
- [ ] Alte delegation.py parallel belassen (Migration)

### Step 2: SessionService erstellen
- [ ] `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`
- [ ] Nutzt session_manager.py für OpenCode API
- [ ] Lifecycle: spawn → query → send → get_output → stop

### Step 3: MCP Tools anpassen
- [ ] server.py: Neue Tool-Namen und Schemas
- [ ] Weiterleitung an SessionService statt DelegationService
- [ ] Alte Tools parallel belassen (deprecated)

### Step 4: Tests aktualisieren
- [ ] test_session_service.py erstellen
- [ ] test_mcp_tools_v2.py für neue Tools
- [ ] Integration Tests mit Mock OpenCode

### Step 5: Cleanup
- [ ] Alte delegation.py deprecaten
- [ ] Alte MCP Tools entfernen
- [ ] Documentation update

## ⚠️ Migrations-Strategie

**Paralleler Betrieb während Migration**:
1. Neue Session-Tools hinzufügen (v2_)
2. Alte Delegation-Tools behalten aber deprecaten
3. Tests für beide Systeme
4. Nach Validierung: Alte Tools entfernen

## 🧪 Test-Plan

### Unit Tests
- [ ] SessionService CRUD
- [ ] OpenCode API Client neue Methods
- [ ] Session Models Validation

### Integration Tests  
- [ ] spawn_agent → OpenCode Session erstellt
- [ ] query_session → Status korrekt
- [ ] send_to_agent → Message delivered
- [ ] stop_agent → Session cleaned up

### E2E Tests
- [ ] PM Agent spawnt Backend Specialist
- [ ] Pollt Zwischenstand
- [ ] Sendet Follow-up
- [ ] Holt finales Ergebnis

## 📅 Timeline

- **Phase 1** (2h): Models + SessionService
- **Phase 2** (2h): MCP Tools Refactoring
- **Phase 3** (1h): Tests
- **Phase 4** (1h): Documentation + Cleanup

**Total**: ~6 Stunden

## ✅ Success Criteria

1. [ ] Alle neuen MCP Tools funktionieren
2. [ ] OpenCode API wird korrekt genutzt
3. [ ] Tests passing (inkl. neue Session Tests)
4. [ ] Documentation aktualisiert
5. [ ] PM Agent kann Agents spawnen und steuern

---

**Status**: Plan erstellt, Ready for Implementation
**Next**: Start mit Phase 1 (Models + SessionService)
