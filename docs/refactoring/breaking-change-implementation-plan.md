# Breaking Change Implementation Plan - ct_dev-agent_delegation

## 🜄 Ziel 🜄
Vollständige Umbenennung und konzeptionelle Umstellung von "Orchestrator/Session" zu "Delegation" gemäß X^∞ Prinzipien.

## 🜄 Kontext 🜄
- Auctor Decision: Sofortige Breaking Changes ohne Übergangsphase
- Branch: feature/opencode-api-integration
- Task-ID: 84811d54-f068-43e9-9905-a70722e73b14
- Philosophie: Cap-Transfer durch explizite Delegation

## 🜄 Verantwortung 🜄
- Entscheidung: Auctor
- Planung: Claude (PLAN mode)
- Umsetzung: Delegation an Experten (EDIT mode)
- Cap: Breaking Change mit X^∞ Alignment

---

## Phase 1: Projekt-Umbenennung

### 1.1 Repository & Package
- [ ] pyproject.toml: name = "ct_dev-agent_delegation"
- [ ] pyproject.toml: package name in dependencies
- [ ] README.md: Alle Referenzen zu ct_dev-agent_orchestrator
- [ ] setup.py (falls vorhanden)

### 1.2 Python Package Struktur
- [ ] src/ct_dev_agent_orchestrator_mcp/ → src/ct_dev_agent_delegation_mcp/
- [ ] Alle Imports aktualisieren (global search/replace)

### 1.3 Konfiguration & Deployment
- [ ] .env Variablen (falls orchestrator erwähnt)
- [ ] Docker/Compose Files
- [ ] CI/CD Pipelines
- [ ] MCP Server Registration

---

## Phase 2: Session → Delegation Model/Service

### 2.1 Models
**File: src/ct_dev_agent_delegation_mcp/models/session.py → delegation.py**

- [ ] Class `Session` → `Delegation`
- [ ] `SpawnAgentRequest` → `SpawnDelegationRequest`
- [ ] Field `session_id` → `delegation_id` (alle Vorkommen)
- [ ] Enum `SessionStatus` → `DelegationStatus` (falls vorhanden)
- [ ] Alle Docstrings anpassen

### 2.2 Services
**File: src/ct_dev_agent_delegation_mcp/services/session_service.py → delegation_service.py**

- [ ] Class `SessionService` → `DelegationService`
- [ ] Method `spawn_agent` → `spawn_delegation`
- [ ] Method `query_session` → `query_delegation`
- [ ] Method `list_active_sessions` → `list_active_delegations`
- [ ] Alle internen Variablen (z.B. `_sessions` → `_delegations`)
- [ ] Alle Docstrings

**session_manager.py:**
- [ ] BEHALTEN (technisch weiterhin korrekt für Session-Management)
- [ ] Aber umbenennen zu process_session_manager.py (Klarheit)

### 2.3 Imports Update
- [ ] server.py: Import-Statements
- [ ] Alle Services die SessionService nutzen
- [ ] Alle Tests

---

## Phase 3: MCP Tools Breaking Changes

### 3.1 Tool Definitionen (server.py)

**Primary Session-based Tools:**
- [ ] `spawn_agent` → `delegate_task`
  - Description: "Delegates a task to a specialized agent..."
  - inputSchema: Parameter-Namen prüfen (task → work?)

- [ ] `query_session` → `query_delegation`
- [ ] `get_agent_output` → `get_delegation_output`
- [ ] `list_active_sessions` → `list_active_delegations`
- [ ] `stop_agent` → `stop_delegation`
- [ ] `send_to_agent` → `send_to_delegation`

**Agent Discovery Tools:**
- [ ] `list_agents` → `list_running_delegations`
  - Description: "Lists currently running delegations (agent instances)"
  
- [ ] `list_opencode_agents` → `list_available_agent_roles`
  - Description: "Lists available agent roles/templates from OpenCode server"

**Redundanz entfernen:**
- [ ] Doppelte `get_agent_capabilities` (Zeile ~231) LÖSCHEN

### 3.2 Tool Handlers (call_tool function)

- [ ] `if name == "spawn_agent":` → `if name == "delegate_task":`
- [ ] `elif name == "query_session":` → `elif name == "query_delegation":`
- [ ] Alle weiteren Handler entsprechend
- [ ] Output-Messages anpassen ("Session" → "Delegation")

---

## Phase 4: Database Schema Migration

### 4.1 Alembic Migration erstellen

```python
# migrations/versions/xxx_session_to_delegation.py

def upgrade():
    # Rename table
    op.rename_table('sessions', 'delegations')
    
    # Rename column
    op.alter_column('delegations', 'session_id', new_column_name='delegation_id')
    
    # Update foreign keys (falls vorhanden)
    # z.B. in anderen Tables die auf session_id referenzieren

def downgrade():
    op.alter_column('delegations', 'delegation_id', new_column_name='session_id')
    op.rename_table('delegations', 'sessions')
```

### 4.2 Database Queries
- [ ] Alle SQL-Queries in storage/database.py
- [ ] ORM-Queries (falls SQLAlchemy)
- [ ] Indizes umbenennen

---

## Phase 5: Interne Referenzen

### 5.1 Variable Names (Global Search/Replace)
- [ ] `session_id` → `delegation_id` (Code)
- [ ] `session_info` → `delegation_info`
- [ ] `active_sessions` → `active_delegations`
- [ ] `_sessions` → `_delegations` (private vars)

### 5.2 Function Parameters
- [ ] Alle function signatures mit session_id
- [ ] Type hints aktualisieren

### 5.3 Comments & Docstrings
- [ ] "session" → "delegation" (wo konzeptionell gemeint)
- [ ] Aber NICHT in "session_manager" (technischer Begriff)

---

## Phase 6: Tests

### 6.1 Test Files
- [ ] tests/test_session_service.py → test_delegation_service.py
- [ ] tests/integration/test_mcp_tools.py (Tool-Namen)
- [ ] Alle test_spawn_agent → test_delegate_task
- [ ] Mock-Daten anpassen

### 6.2 Fixtures
- [ ] session_fixture → delegation_fixture
- [ ] mock_session → mock_delegation

---

## Phase 7: Dokumentation

### 7.1 README.md
- [ ] Projekt-Name
- [ ] Installation Instructions
- [ ] MCP Tool Examples (neue Namen)
- [ ] Architecture Diagramm

### 7.2 API Dokumentation
- [ ] docs/api.md (falls vorhanden)
- [ ] MCP Tool Schema
- [ ] Migration Guide für Clients

### 7.3 CHANGELOG.md

```markdown
## [2.0.0] - BREAKING CHANGES - 2025-10-03

### Changed
- **BREAKING**: Projekt umbenannt zu `ct_dev-agent_delegation`
- **BREAKING**: Alle "Session" Konzepte zu "Delegation" umbenannt
- **BREAKING**: MCP Tools umbenannt:
  - spawn_agent → delegate_task
  - query_session → query_delegation
  - get_agent_output → get_delegation_output
  - list_active_sessions → list_active_delegations
  - stop_agent → stop_delegation
  - send_to_agent → send_to_delegation
  - list_agents → list_running_delegations
  - list_opencode_agents → list_available_agent_roles

### Removed
- **BREAKING**: Doppelte get_agent_capabilities Definition entfernt

### Migration Guide
1. Update MCP Client Tool calls (siehe neue Namen)
2. Database Migration ausführen: `alembic upgrade head`
3. Imports aktualisieren: ct_dev_agent_orchestrator → ct_dev_agent_delegation
4. session_id → delegation_id in allen API-Calls
```

---

## Phase 8: Validierung

### 8.1 Pre-Deployment Checks
- [ ] Alle Tests grün
- [ ] Type Checking (mypy)
- [ ] Linting (ruff)
- [ ] Import-Validierung

### 8.2 Integration Tests
- [ ] MCP Server startet
- [ ] delegate_task funktioniert
- [ ] Database Migration erfolgreich
- [ ] Alle Tools verfügbar

---

## Umsetzungs-Reihenfolge (KRITISCH)

1. **Phase 2** (Models/Services) ZUERST
   - Interne Struktur ohne External Break
   
2. **Phase 4** (Database) DANACH
   - Schema-Migration
   
3. **Phase 3** (MCP Tools) DANN
   - External Breaking Changes
   
4. **Phase 1** (Projekt-Name) DANN
   - Package-Umbenennung
   
5. **Phase 5-7** (Rest) PARALLEL
   - Cleanup & Docs

6. **Phase 8** (Validierung) FINAL
   - Tests & Deployment

---

## Risiko-Mitigation

### Database Migration
**Risiko:** Datenverlust
**Mitigation:** 
- Backup vor Migration
- Rollback-Script testen
- Downgrade-Path in Alembic

### MCP Client Breaks
**Risiko:** Alle Clients offline
**Mitigation:**
- Migration-Guide bereitstellen
- Koordination mit Client-Teams
- Status-Page während Migration

### Import-Chaos
**Risiko:** Circular imports
**Mitigation:**
- Reihenfolge einhalten
- Pro Phase testen
- Import-Graph validieren

---

## Geschätzte Dauer

| Phase | Dauer | Kritikalität |
|-------|-------|--------------|
| 1. Projekt-Umbenennung | 2h | HIGH |
| 2. Model/Service | 3h | HIGH |
| 3. MCP Tools | 2h | HIGH |
| 4. Database | 2h | HIGH |
| 5. Referenzen | 2h | MEDIUM |
| 6. Tests | 3h | HIGH |
| 7. Docs | 2h | MEDIUM |
| 8. Validierung | 2h | HIGH |
| **TOTAL** | **18h** | - |

---

## 🜄 Nächste Schritte 🜄

**Freigabe erforderlich:**
- [ ] Auctor Approval für Umsetzungsplan
- [ ] Team-Koordination für Client-Migration
- [ ] Downtime-Window festlegen

**Nach Freigabe:**
- [ ] Branch erstellen: `breaking/session-to-delegation`
- [ ] Phase 2 delegieren an Backend Specialist
- [ ] Phase 4 delegieren an Database Expert
- [ ] Parallel: Phase 6 an Test Specialist

## 🜄 Verantwortung Final 🜄
- Plan: Claude (Completed)
- Freigabe: **AUCTOR** (Pending)
- Umsetzung: Delegation an Experten nach Freigabe
