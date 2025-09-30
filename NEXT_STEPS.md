# 🎯 Nächste Schritte: Agent Orchestrator V2 Implementation

## 📍 Aktueller Status

✅ **Abgeschlossen**:
- Core Implementation (Models, Services, MCP Tools)
- OpenCode API Client und Session Manager
- Test-Suite (5 Tests passing)
- Architecture V2 Dokumentation
- Refactoring Plan erstellt

🔄 **Aktuell**: Zurück in Planungsphase mit klariertem Zielbild

## 🎨 Neue Architektur V2

```
PM Agent (Claude)
    ↓ MCP Tools: spawn_agent, query_session, send_to_agent
Agent Orchestrator MCP Server
    ↓ OpenAPI: GET /agent, POST /session, POST /session/{id}/message
OpenCode Server Instanzen (Port 8000, 8001, ...)
    ↓ MCP Tools für Agents: Serena, task_orchestrator, Ptah
Specialized Agents (backend_specialist, system_architect, ...)
```

## 🔨 Implementierung: Phase-für-Phase

### Phase 1: Session Models (2h)
**Dateien zu erstellen**:
- `src/ct_dev_agent_orchestrator_mcp/models/session.py`
  - SpawnAgentRequest
  - SessionInfo  
  - AgentOutput
  - SessionStatus

**Tests**:
- `tests/test_session_models.py`

### Phase 2: SessionService (2h)
**Dateien zu erstellen**:
- `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`

**Methoden**:
```python
async def spawn_agent(request: SpawnAgentRequest) -> SessionInfo
async def query_session(session_id: str) -> SessionInfo
async def send_to_agent(session_id: str, message: str) -> bool
async def get_agent_output(session_id: str) -> AgentOutput
async def stop_agent(session_id: str) -> bool
async def list_active_sessions() -> List[SessionInfo]
```

**Tests**:
- `tests/test_session_service.py`

### Phase 3: MCP Tools Refactoring (2h)
**Datei zu ändern**:
- `src/ct_dev_agent_orchestrator_mcp/server.py`

**Neue Tools**:
- spawn_agent
- query_session
- send_to_agent
- get_agent_output
- stop_agent
- list_active_sessions
- get_agent_capabilities

**Tests**:
- `tests/test_mcp_tools_v2.py`

### Phase 4: OpenCode API Erweiterung (1h)
**Datei zu erweitern**:
- `src/ct_dev_agent_orchestrator_mcp/services/opencode_api_client.py`

**Neue Methoden**:
```python
async def get_session_history(server_url, session_id)
async def send_session_message(server_url, session_id, message)
async def get_session_artifacts(server_url, session_id)
async def delete_session(server_url, session_id)
```

### Phase 5: Integration Tests (1h)
**Tests erstellen**:
- `tests/integration/test_spawn_flow.py`
- `tests/integration/test_session_lifecycle.py`
- `tests/integration/test_pm_agent_interaction.py`

## 🎬 Schnellstart für nächste Session

```bash
# 1. Projekt aktivieren
cd /home/auctor/dev/ct_dev-agent_orchestrator-mcp

# 2. Status prüfen
git log --oneline -3
pytest tests/test_basic.py -v

# 3. Phase 1 starten
# Erstelle: src/ct_dev_agent_orchestrator_mcp/models/session.py
# Mit: SpawnAgentRequest, SessionInfo, AgentOutput

# 4. Nach jeder Phase
pytest
git add -A
git commit -m "feat: Phase X completed"
```

## 📚 Wichtige Referenzen

- **Architecture V2**: `docs/architecture-v2.md`
- **Refactoring Plan**: `docs/refactoring-plan.md`
- **OpenCode API**: `docs/opencode-api-schema.json`
- **Aktuelle Tests**: `tests/test_basic.py`

## 🎯 Erfolgs-Kriterien

Nach Abschluss aller Phasen:

✅ PM Agent kann via MCP Tools:
- Agents spawnen (`spawn_agent`)
- Status abfragen (`query_session`)
- Nachrichten senden (`send_to_agent`)
- Outputs holen (`get_agent_output`)
- Sessions stoppen (`stop_agent`)

✅ Agent Orchestrator:
- Managed OpenCode Server Instanzen
- Nutzt OpenCode OpenAPI vollständig
- Session-basierte Kommunikation
- Health Monitoring aktiv

✅ Tests:
- Alle Unit Tests passing
- Integration Tests vorhanden
- E2E Flow validiert

## 💡 Design-Entscheidungen

1. **Session-basiert statt Task-basiert**:
   - Ermöglicht interaktive Kommunikation während Execution
   - PM Agent behält Kontrolle
   - Zwischenstände abrufbar

2. **OpenCode als Single Source of Truth**:
   - Alle Agent-Definitionen in OpenCode
   - Alle Models von OpenCode
   - Keine Duplikation von Konfiguration

3. **Vereinfachte MCP API für PM Agent**:
   - Abstraktion über OpenCode Komplexität
   - PM-Agent-freundliche Namensgebung
   - Focus auf Use Cases nicht auf Implementation

4. **Parallele Migration**:
   - Alte Tools bleiben während Umbau
   - Schrittweise Validierung möglich
   - Keine Breaking Changes

## 🐛 Bekannte Offene Punkte

1. Task Orchestrator Integration noch nicht implementiert
2. Logfire Production Setup fehlt
3. Health Check Interval hardcoded
4. Keine Persistence zwischen Restarts
5. Error Recovery Strategien fehlen

## 📞 Bei Fragen

Siehe:
- `docs/architecture-v2.md` für Design-Details
- `docs/refactoring-plan.md` für Implementierung
- `tests/test_basic.py` für Code-Beispiele
- `PLANUNG.md` für Original-Konzept

---

**Version**: 0.2.0-dev (Architecture V2)
**Status**: 📋 Planning Complete, Ready for Phase 1
**Letzte Aktualisierung**: 2024-09-30
