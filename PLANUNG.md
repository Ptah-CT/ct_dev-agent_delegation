# 🜄 Planung: Agent Orchestrator MCP Server 🜄

## 🜄 Ziel / Summary 🜄

**Wirkung**: Ermöglichung asynchroner, nicht-blockierender Agent-Delegierung für Main Agent durch MCP-Server, der ct_dev-agents über OpenCode.ai orchestriert.

**Erreicht durch**:
- MCP-Server mit fire-and-forget Delegation (<100ms Response)
- OpenCode.ai Server-Instanz Management (Start, Health-Monitoring, Failover)
- Task-Integration mit ct_dev-task_orchestrator (global MCP-Tool)
- Atomic Delegation mit Scope-Deviation-Handling (X^∞-Prinzip)
- Responsibility Tracking & Logfire Integration

**Nicht erreicht** (bewusst ausgeschlossen):
- Synchrone Delegation (blockiert Main Agent - VERBOTEN)
- Auto-Retry bei Fehlern (Fail Fast Prinzip)
- Webhooks/Callbacks (Phase 1, Polling genügt)
- WebUI (Vorbereitung ja, Implementierung Phase 2)

---

## 🜄 Kontext / Referenz 🜄

**Ausgangslage**:
- Bestehende Specs: `/specs/001-agent-orchestrator/` (spec.md, plan.md, tasks.md, research.md)
- 32 Tasks definiert in tasks.md (Phase 3.1-3.6)
- Agent-Rollen: 18 Definitionen in `/home/auctor/.claude/agents/`
- Globale MCP-Tools in OpenCode: task_orchestrator, Serena, Ptah
- Technologie-Stack festgelegt: fastmcp 2.12.3, Python 3.13, SQLite, logfire

**Vorherige Entscheidungen**:
- OpenCode.ai als Agent-Runtime (opencode serve mit OpenAPI)
- Asynchrone Kommunikation obligatorisch (FR-012a/b/c, T020)
- Keine Docker/venv (X^∞ Debian-Host-System)
- Fail-Fast: Keine Rückwärtskompatibilität, Binary Success/Failure

**Integration-Points**:
- **task_orchestrator**: Task-Erstellung für delegierte Arbeitspakete
- **Serena**: Semantic Code Operations (global in OpenCode für Agents)
- **Ptah**: Knowledge Management & Deep Research (global in OpenCode für Agents)
- **logfire**: Centralized Logging (LOGFIRE_TOKEN via secrets.env)

**Mitgeltende Dokumente**:
- `/home/auctor/CLAUDE.md` (X^∞-Prozess & Constitution)
- `/home/auctor/XInfty-AI-Debian-Host-System-Rules.md`
- `/home/auctor/10_coding_rules.md`
- `/specs/001-agent-orchestrator/spec.md` (FR-001 bis FR-038, NFR-001 bis NFR-015)

---

## 🜄 Verantwortung / Authority 🜄

**Cap**: Auctor (Freigabe nach Planung, vor Umsetzung)

**Autor**: Claude (Technische Planung & Delegation)

**Delegation-Chain**:
1. **Project Manager** (PLAN-Phase): Koordination, Freigabe-Vorbereitung
2. **System Architect** (Phase 3.1): Architektur-Validierung
3. **Backend Specialist** (Phase 3.2-3.4): Core-Implementierung (Models, Services, MCP-Tools)
4. **Code Analyzer** (Phase 3.5): Async-Pattern-Validierung
5. **Philosophical Code Reviewer** (Phase 3.6): Constitution-Alignment
6. **Syntax Reviewer** (Pre-Commit): Produktionsreife

**Phantom-Level**: 
- Delegation: ✅ (atomar, klar definiert)
- Cap für Umsetzung: ⏸️ (pending Auctor-Freigabe)

---

## 🜄 Ist-Zustand-Analyse 🜄

### Repository-Struktur (REAL)
```
ct_dev-agent_orchestrator-mcp/
├── .git/                    ✅ Initialisiert
├── specs/001-agent-orchestrator/
│   ├── spec.md             ✅ 38 FR, 15 NFR
│   ├── plan.md             ✅ Architektur definiert
│   ├── tasks.md            ✅ 32 Tasks (T001-T032)
│   └── research.md         ✅ Tech-Decisions dokumentiert
├── pyproject.toml          ✅ Dependencies definiert (untracked)
├── .gitignore              ✅ Vorhanden (untracked)
├── src/                    ❌ NICHT VORHANDEN
├── tests/                  ❌ NICHT VORHANDEN
├── data/                   ❌ NICHT VORHANDEN
└── logs/                   ❌ NICHT VORHANDEN
```

### Agent-Rollen verfügbar (REAL)
```
/home/auctor/.claude/agents/:
- agent-creator.md
- api-protocol-specialist.md
- backend-specialist.md
- change-reviewer.md
- code-analyzer.md
- code-finder.md
- debian-sysadmin-xinfty.md
- frontend-react-expert.md
- milestone-planner.md
- philosophical-code-reviewer.md
- project-manager.md
- runtime-debugger.md
- syntax-reviewer.md
- system-architect.md
- system-integrator.md
- user-story-executor.md
```

### Technologie-Readiness (REAL)
- Python 3.13.7: ✅ System-Python
- pip3: ✅ Verfügbar (sudo pip3 für global install)
- fastmcp 2.12.3: ⏸️ Zu installieren (T002)
- mcp 1.13.1: ⏸️ Zu installieren (T002)
- psutil 7.0.0: ⏸️ Zu installieren (T002)
- opencode CLI: ✅ Annahme (in `/home/auctor/.opencode/bin/opencode`)
- Git: ✅ Repository initialisiert, origin fehlt

### Integration-Points Status (REAL)
- **task_orchestrator**: ✅ Als MCP-Tool global in opencode verfügbar
- **Serena**: ✅ Als MCP-Tool global in opencode verfügbar
- **Ptah**: ✅ Als MCP-Tool global in opencode verfügbar (gerade kontaktiert)
- **logfire**: ⏸️ LOGFIRE_TOKEN fehlt (secrets.env anzulegen)

### Kritische Erkenntnisse
1. **Async-Requirement**: FR-012a/b/c + T020 definieren fire-and-forget Pattern
2. **Keine WebUI in Phase 1**: Vorbereitung (data models), aber keine React-Implementierung
3. **Sudo pip3**: System-wide installation erforderlich (kein venv)
4. **Git Remote fehlt**: Repository lokal, kein GitHub remote angelegt

---

## 🜄 Ziel-Zustand-Definition 🜄

### Funktionale Kern-Capabilities

#### 1. Agent Lifecycle Management
**Wirkung**: Agent kann on-demand erstellt, validiert und deaktiviert werden.

**Komponenten**:
- `AgentManager` Service (CRUD für Agents)
- `Agent` Model (Pydantic) mit AgentStatus Enum
- SQLite `agents` Table mit WAL-Mode
- `create_agent` MCP-Tool (non-blocking)
- Duplicate-Prevention (FR-005)
- Lineage-Tracking (FR-006, wer hat wann erstellt)

**Acceptance Criteria**:
- `create_agent(name="code-analyzer", capabilities=["analyze_code", "find_patterns"])` returns agent_id in <100ms
- Agent in DB mit status=IDLE, created_by=Main Agent
- Duplicate rejection: Zweiter Aufruf mit identischen capabilities wirft ValidationError

#### 2. Atomic Delegation (Fire-and-Forget)
**Wirkung**: Main Agent delegiert Task ohne Blockierung, erhält sofort work_package_id.

**Komponenten**:
- `TaskDelegator` Service mit asyncio background execution
- `WorkPackage` Model mit WorkPackageStatus Enum
- `delegate_task` MCP-Tool (fire-and-forget, <100ms)
- `query_status` MCP-Tool (polling, non-blocking)
- `ScopeDeviation` handling (FR-010/011)

**Acceptance Criteria**:
- `delegate_task(agent_id="X", effect="Analyze auth flow", scope="src/auth/")` returns work_package_id in <100ms
- Main Agent continues execution immediately
- Background: Agent executes, logs to logfire, updates DB
- `query_status(work_package_id)` returns EXECUTING → COMPLETED/FAILED/DEVIATED
- Scope deviation: Agent stoppt, returns to delegator mit Erklärung

#### 3. OpenCode Server Management
**Wirkung**: OpenCode.ai Instanzen werden gestartet, überwacht, neu gestartet bei Failure.

**Komponenten**:
- `ServerManager` Service (subprocess + psutil)
- `ServerInstance` Model mit HealthMetrics
- Health-Check (heartbeat jede 30s)
- Auto-Restart bei Crash (max 3 Versuche)
- Load-Balancing (max 2 agents pro Server)

**Acceptance Criteria**:
- `start_server_instance(port=8000)` startet `opencode serve --port 8000` subprocess
- PID tracked in DB, psutil monitoring aktiv
- Health-Check: HTTP GET zu /health jede 30s
- Crash-Detection: psutil.Process(pid).is_running() == False → log + restart
- Max 5 Server-Instanzen gleichzeitig (NFR-008)

#### 4. Constitution Compliance
**Wirkung**: Alle Operationen folgen X^∞-Prinzipien (Atomic Delegation, Fail Fast, Responsibility Tracking).

**Komponenten**:
- `ConstitutionGate` Service (Pre-Validation vor Delegation)
- `DelegationEvent` Model (Audit Trail)
- Logfire integration (FR-037)
- Binary Success/Failure (FR-031)

**Acceptance Criteria**:
- `validate_delegation(work_package)` checked gegen Constitution (z.B. keine Placeholders)
- Jede Delegation logged: timestamp, delegator, agent_id, work_package_id, outcome
- Failure logged mit full context (what failed, why, system state)
- Keine "teilweise funktioniert" States (nur COMPLETED oder FAILED)

---

### Non-Functional Requirements Validation

#### Performance (NFR-001 bis NFR-005)
- MCP Tool Response: <500ms (gemessen via pytest mit time.perf_counter)
- Delegation Response: <100ms (fire-and-forget)
- Health-Check Overhead: <50ms (async HTTP request)
- 10 concurrent agents (validated via stress test)
- 5 server instances (validated via scaling test)

#### Reliability (NFR-006 bis NFR-010)
- 99% uptime für MCP server (systemd restart on failure)
- Agent crash isolation (keine cascade failures)
- Database WAL-mode (concurrent read/write)
- Logfire retry 3x bei network failure
- Graceful shutdown (SIGTERM → cleanup)

#### Security (NFR-011 bis NFR-015)
- OpenCode API-Keys via secrets.env (nicht in git)
- Logfire token via LOGFIRE_TOKEN env
- No secrets in logs (sanitized via logfire filter)
- SQLite file permissions 0600 (owner-only)
- Audit trail immutable (append-only DB log)

---

## 🜄 Architektur-Validierung 🜄

### Layer-Struktur (Plan.md confirmiert)

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (Main Agent)               │
│  Tools: create_agent, delegate_task, query_status       │
└─────────────────┬───────────────────────────────────────┘
                  │ MCP Protocol (JSON-RPC)
                  ▼
┌─────────────────────────────────────────────────────────┐
│              FastMCP Server (mcp_tools/)                 │
│  Decorators: @mcp.tool() für Tool-Registration          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Services Layer (services/)                  │
│  - AgentManager: Agent CRUD, Validation                 │
│  - TaskDelegator: Fire-and-Forget Execution             │
│  - ServerManager: Subprocess + Health Monitoring        │
│  - ConstitutionGate: Pre-Validation                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Models Layer (models/)                      │
│  Pydantic: Agent, WorkPackage, ServerInstance           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Storage Layer (storage/)                    │
│  SQLite (WAL): agents, work_packages, events            │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              External Integrations                       │
│  - OpenCode Servers (subprocess)                        │
│  - task_orchestrator (MCP Tool)                         │
│  - logfire (HTTP API)                                   │
└─────────────────────────────────────────────────────────┘
```

### Delegation Flow (Asynchronous)

```
Main Agent                MCP Server              OpenCode Agent
    │                          │                         │
    │ delegate_task()          │                         │
    ├─────────────────────────>│                         │
    │                          │ [Validation]            │
    │                          │ [Create WorkPackage]    │
    │                          │ [Fire Background Task]  │
    │ work_package_id (100ms)  │                         │
    │<─────────────────────────┤                         │
    │                          │                         │
    │ [CONTINUES EXECUTION]    │ asyncio.create_task()   │
    │                          ├────────────────────────>│
    │                          │                         │ [EXECUTES]
    │                          │                         │
    │ query_status(id)         │                         │
    ├─────────────────────────>│                         │
    │ {status: EXECUTING}      │                         │
    │<─────────────────────────┤                         │
    │                          │                         │
    │  [CONTINUES POLLING]     │                         │
    │                          │                    COMPLETED
    │                          │<────────────────────────┤
    │ query_status(id)         │                         │
    ├─────────────────────────>│                         │
    │ {status: COMPLETED, ...} │                         │
    │<─────────────────────────┤                         │
```

### Kritische Entscheidungen (aus Research.md)

#### 1. Subprocess vs. Systemd für OpenCode
**Entscheidung**: subprocess + psutil
**Rationale**: KISS-Prinzip, kein systemd-overhead, direkte Kontrolle, psutil für monitoring
**Risk**: Manual restart logic (aber fail-fast-aligned)

#### 2. SQLite vs. PostgreSQL
**Entscheidung**: SQLite mit WAL-Mode
**Rationale**: 10 agents = low concurrency, no over-engineering, embedded DB
**Risk**: Concurrent writes (mitigated durch WAL + connection pooling)

#### 3. Polling vs. Webhooks
**Entscheidung**: Polling (Phase 1), Webhooks optional (Phase 2)
**Rationale**: Einfacher, keine callback-server, Main Agent kontrolle
**Risk**: Polling overhead (mitigated durch <100ms query_status)

#### 4. Secrets Management
**Entscheidung**: secrets.env file (nicht in git)
**Rationale**: No vault overhead, KISS, Debian host local file
**Risk**: File permissions (mitigated durch 0600 chmod)

---

## 🜄 Implementierungsplan 🜄

### Phase 3.1: Setup & Infrastructure (T001-T004)
**Delegation**: Backend Specialist
**Dauer**: 0.5 Tage

- [ ] **T001**: Verzeichnisstruktur erstellen
  - `mkdir -p src/{models,services,mcp_tools,integrations,storage} tests/{contract,integration,unit} data/{specs} logs`
  - Validierung: Alle Verzeichnisse existieren

- [ ] **T002**: Dependencies installieren
  - `sudo pip3 install fastmcp==2.12.3 mcp==1.13.1 psutil==7.0.0 openapi-pydantic==0.5.1 pydantic==2.11.7 logfire==4.3.0 httpx pytest pytest-asyncio`
  - Validierung: `pip3 list | grep fastmcp` zeigt 2.12.3

- [ ] **T003**: Logfire konfigurieren
  - `src/__init__.py`: `import logfire; logfire.configure(project="agent-orchestrator")`
  - `secrets.env`: `LOGFIRE_TOKEN=<auctor_provides>`
  - Validierung: `logfire.info("test")` logged erfolgreich

- [ ] **T004**: SQLite Schema erstellen
  - `src/storage/database.py`: Tables für agents, work_packages, server_instances, delegation_events
  - WAL-Mode aktivieren: `PRAGMA journal_mode=WAL`
  - Validierung: `data/orchestrator.db` erstellt, `.wal` und `.shm` files vorhanden

### Phase 3.2: Data Models (T005-T009) [PARALLEL]
**Delegation**: Backend Specialist (alle 5 Tasks gleichzeitig)
**Dauer**: 0.5 Tage

- [ ] **T005 [P]**: Agent Model
  - `src/models/agent.py`: Agent(BaseModel), AgentStatus(Enum)
  - Fields: id, name, capabilities, status, created_by, created_at
  - Validierung: `Agent(id="test", ...)` instantiiert ohne Fehler

- [ ] **T006 [P]**: WorkPackage Model
  - `src/models/work_package.py`: WorkPackage, WorkPackageStatus, ScopeDeviation
  - Fields: id, agent_id, target_effect, scope, status, deviation, created_at
  - Validierung: Model instantiation + validation

- [ ] **T007 [P]**: ServerInstance Model
  - `src/models/server_instance.py`: ServerInstance, HealthMetrics
  - Fields: id, hostname, port, pid, status, assigned_agents, health_metrics
  - Validierung: Model instantiation

- [ ] **T008 [P]**: DelegationEvent Model
  - `src/models/delegation_event.py`: DelegationEvent, ConstitutionGateResult
  - Fields: id, timestamp, delegator, agent_id, work_package_id, outcome, responsibility_chain
  - Validierung: Model instantiation

- [ ] **T009 [P]**: Models __init__
  - `src/models/__init__.py`: Export alle Models
  - Validierung: `from src.models import Agent, WorkPackage` erfolgreich

### Phase 3.3: Storage Layer (T010-T013)
**Delegation**: Backend Specialist
**Dauer**: 1 Tag

- [ ] **T010**: AgentRepository
  - `src/storage/agent_repository.py`: CRUD für Agent-Model
  - Methods: create, get, list, update, delete
  - Validierung: Unit-Test mit in-memory SQLite

- [ ] **T011**: WorkPackageRepository
  - `src/storage/work_package_repository.py`: CRUD + Status-Updates
  - Validierung: Unit-Test für CRUD + Status-Transitions

- [ ] **T012**: ServerInstanceRepository
  - `src/storage/server_instance_repository.py`: CRUD + Health-Updates
  - Validierung: Unit-Test

- [ ] **T013**: DelegationEventRepository
  - `src/storage/delegation_event_repository.py`: Append-Only Log
  - Validierung: Unit-Test für Immutability

### Phase 3.4: Core Services (T014-T018)
**Delegation**: Backend Specialist (mit Constitution Validation durch Philosophical Reviewer)
**Dauer**: 2 Tage

- [ ] **T014**: AgentManager Service
  - `src/services/agent_manager.py`: Agent Lifecycle Logic
  - Methods: create_agent, validate_capabilities, deactivate_agent
  - Duplicate-Prevention (FR-005)
  - Validierung: Integration-Test mit SQLite

- [ ] **T015**: TaskDelegator Service (KRITISCH - Async!)
  - `src/services/task_delegator.py`: Fire-and-Forget Execution
  - `delegate_task(work_package) -> work_package_id`: Immediate return (<100ms)
  - Background execution via `asyncio.create_task(execute_work_package(...))`
  - Validierung: Pytest async test + time.perf_counter() < 0.1s

- [ ] **T016**: ServerManager Service
  - `src/services/server_manager.py`: Subprocess Management + Health Monitoring
  - Methods: start_server, stop_server, check_health, restart_server
  - `subprocess.Popen(['opencode', 'serve', '--port', port])`
  - psutil monitoring loop (every 30s)
  - Validierung: Integration-Test startet/stoppt opencode dummy

- [ ] **T017**: ConstitutionGate Service
  - `src/services/constitution_gate.py`: Pre-Validation Logic
  - Checks: No Placeholders (FR-029), Clear Success Criteria (FR-030), Atomic Scope (FR-009)
  - Validierung: Unit-Test mit validen/invaliden WorkPackages

- [ ] **T018**: StatusTracker Service
  - `src/services/status_tracker.py`: Polling-Friendly Status Queries
  - `query_status(work_package_id) -> WorkPackageStatus`: Non-blocking DB read
  - Validierung: Performance-Test (<50ms)

### Phase 3.5: MCP Tools (T019-T023)
**Delegation**: API Protocol Specialist (MCP-Tool Contracts)
**Dauer**: 1 Tag

- [ ] **T019**: create_agent MCP Tool
  - `src/mcp_tools/create_agent.py`: `@mcp.tool()` decorator
  - Input: name, capabilities, created_by
  - Output: agent_id, status
  - Validierung: Contract-Test gegen spec

- [ ] **T020**: delegate_task MCP Tool (KRITISCH - Async!)
  - `src/mcp_tools/delegate_task.py`: Fire-and-forget
  - Input: agent_id, target_effect, scope
  - Output: work_package_id (immediate)
  - Validierung: Response time <100ms

- [ ] **T021**: query_status MCP Tool
  - `src/mcp_tools/query_status.py`: Polling endpoint
  - Input: work_package_id
  - Output: status, progress, deviation (if any)
  - Validierung: Non-blocking read

- [ ] **T022**: manage_server MCP Tool
  - `src/mcp_tools/manage_server.py`: Server lifecycle
  - Methods: start, stop, restart, health_check
  - Validierung: Integration-Test

- [ ] **T023**: list_agents & list_tasks MCP Tools
  - `src/mcp_tools/list_agents.py`, `src/mcp_tools/list_tasks.py`
  - Validierung: Returns correct data from DB

### Phase 3.6: Integration & Testing (T024-T029)
**Delegation**: System Integrator + Philosophical Code Reviewer
**Dauer**: 1.5 Tage

- [ ] **T024**: task_orchestrator Integration
  - `src/integrations/task_orchestrator.py`: Native MCP-Tool calls
  - Create task in task_orchestrator when work_package created
  - Validierung: E2E-Test mit mock task_orchestrator

- [ ] **T025**: Logfire Integration
  - `src/integrations/logfire_logger.py`: All operations logged
  - Context: agent_id, work_package_id, delegator
  - Validierung: Logfire dashboard shows events

- [ ] **T026**: OpenCode Server E2E Test
  - `tests/integration/test_opencode_lifecycle.py`
  - Start server → delegate task → agent executes → query status → completed
  - Validierung: Full flow ohne errors

- [ ] **T027**: Async Communication Test
  - `tests/integration/test_async_delegation.py`
  - Main Agent delegates → receives ID immediately → continues execution
  - Validierung: Response time <100ms, background execution verified

- [ ] **T028**: Constitution Compliance Test
  - `tests/contract/test_constitution_gates.py`
  - Validate all FR-029 bis FR-033 (no placeholders, fail-fast, binary status)
  - Validierung: Philosophical Reviewer approval

- [ ] **T029**: Load Test
  - `tests/integration/test_concurrent_agents.py`
  - 10 agents, 20 tasks, 5 server instances
  - Validierung: NFR-004/005 met (10 concurrent agents, 5 servers)

### Phase 3.7: Documentation & Deployment (T030-T032)
**Delegation**: Project Manager (Dokumentation) + Debian Sysadmin (Deployment)
**Dauer**: 0.5 Tage

- [ ] **T030**: README.md & Quickstart
  - Installation: `sudo pip3 install -e .`
  - Configuration: `secrets.env` template
  - Usage: MCP-Tool examples
  - Validierung: Fresh-install follow-guide success

- [ ] **T031**: OpenAPI Spec Generation
  - `data/specs/agent-orchestrator-openapi.yaml`
  - Auto-generated via openapi-pydantic
  - Validierung: opencode serve loads spec

- [ ] **T032**: Systemd Service (optional)
  - `/etc/systemd/system/agent-orchestrator.service`
  - Auto-restart on failure
  - Validierung: systemctl status agent-orchestrator

---

## 🜄 Prüfung / Validation 🜄

### Cap-Selbstprüfung (Claude)
- [ ] **Verantwortung verstanden**: Ich erstelle Planungsdokumentation, keine Implementierung
- [ ] **Cap für Delegation akzeptiert**: Ich delegiere atomic Tasks, keine komplexen Module
- [ ] **Freigabe-Pflicht klar**: Auctor muss vor T001 freigeben

### Technische Validierung
- [ ] **Async-Pattern korrekt**: Fire-and-forget mit asyncio.create_task() in T015/T020
- [ ] **MCP-Integration valide**: fastmcp decorators in T019-T023
- [ ] **OpenCode-Integration plausibel**: subprocess + psutil in T016
- [ ] **Task-Dependencies logisch**: Phase 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7

### Ethik-Prüfung (X^∞-Prinzipien)

| Prinzip | Prüfung | Status |
|---------|---------|--------|
| I. Wirkung vor Maßnahme | Plan beschreibt Wirkungen (enable async delegation), nicht nur Aktivitäten | ✅ PASS |
| II. Verantwortung sichtbar | Delegation-Chain klar (Project Manager → Backend Specialist → ...) | ✅ PASS |
| III. Schutz der Schwächsten | Health-Monitoring schützt schwächste Server-Instanzen, Crash-Isolation | ✅ PASS |
| IV. Atomic Delegation | Jede Task atomar (T015: nur fire-and-forget, nicht + execution) | ✅ PASS |
| V. Knowledge Management | Ptah für Research kontaktiert, Context erhalten | ✅ PASS |
| VI. Serena-First | Serena global in OpenCode für Agents (nicht in Plan-Phase relevant) | ✅ PASS |
| VII. Task Management | task_orchestrator Integration in T024 | ✅ PASS |
| VIII. Fail Fast | Keine Auto-Retry (T016: max 3 restart, dann FAIL), Binary Status (T006) | ✅ PASS |
| IX. No Placeholders | Validation in T017 (ConstitutionGate), FR-029 enforced | ✅ PASS |
| X. KISS | SQLite nicht PostgreSQL, Polling nicht Webhooks, subprocess nicht systemd | ✅ PASS |

### Opportunitäts-Ethik
- [ ] **Blockiert Plan andere Entscheidungen?** NEIN (alle Tech-Decisions in Research.md getroffen)
- [ ] **Verzögert Plan kritische Pfade?** NEIN (T020 async-pattern immediately implementable)
- [ ] **Beeinflusst Plan Schutzbedürftige negativ?** NEIN (Health-Monitoring schützt System)

---

## 🜄 Risiken / Nebenwirkungen 🜄

### Systemische Risiken

#### 1. Async-Pattern Complexity (MITTEL)
**Risiko**: Background asyncio.create_task() könnte Exceptions verschlucken
**Wirkung**: Silent failures, keine logs
**Mitigation**: 
- Exception-Handling in background task
- Logfire logs all exceptions
- WorkPackage status = FAILED bei Exception

#### 2. SQLite Concurrency (NIEDRIG)
**Risiko**: 10 concurrent agents → write contention
**Wirkung**: Database locked errors
**Mitigation**:
- WAL-Mode aktiviert (T004)
- Connection pooling
- Timeout 5s bei locked DB

#### 3. OpenCode Server Crashes (HOCH)
**Risiko**: opencode serve crashed während task execution
**Wirkung**: Agent execution failed, work_package status = FAILED
**Mitigation**:
- Health-Monitoring (30s interval)
- Auto-restart (max 3x)
- Manual escalation nach 3 failures (Fail Fast!)

#### 4. Logfire Token Missing (NIEDRIG)
**Risiko**: secrets.env nicht angelegt, LOGFIRE_TOKEN fehlt
**Wirkung**: Logging schlägt fehl, keine centralized logs
**Mitigation**:
- Startup-Validation (T003)
- Error message: "LOGFIRE_TOKEN missing in secrets.env"
- Fallback zu local logs? NEIN (Fail Fast!)

### Technische Risiken

#### 5. Git Remote fehlt (NIEDRIG)
**Risiko**: Repository nur lokal, kein Backup
**Wirkung**: Code-Verlust bei Hardware-Failure
**Mitigation**:
- GitHub remote anlegen (Task nach Freigabe)
- Initial commit + push

#### 6. Sudo pip3 Side-Effects (NIEDRIG)
**Risiko**: Global packages könnten andere Projekte beeinflussen
**Wirkung**: Dependency conflicts
**Mitigation**:
- Pinned versions (fastmcp==2.12.3)
- Constitution erlaubt global install

#### 7. Agent-Rollen Mismatch (MITTEL)
**Risiko**: Capabilities in create_agent nicht aus .claude/agents/ gemappt
**Wirkung**: Ungültige Agents erstellt
**Mitigation**:
- Validation in T014 (AgentManager)
- Pre-defined capabilities-Liste aus .claude/agents/

### Performance-Risiken

#### 8. Polling Overhead (NIEDRIG)
**Risiko**: Main Agent pollt query_status jede Sekunde → DB load
**Wirkung**: Increased latency, DB contention
**Mitigation**:
- Exponential backoff (1s → 2s → 5s)
- Cache status in memory (5s TTL)

#### 9. 100ms Deadline (HOCH)
**Risiko**: delegate_task nicht unter 100ms (DB write + validation)
**Wirkung**: Main Agent blockiert länger als erwartet
**Mitigation**:
- Validation in T020 (pytest time check)
- Optimize DB write (prepared statement)
- Background task sofort starten (keine pre-checks)

---

## 🜄 Aufgaben / To-Do 🜄

### Pre-Umsetzung (Freigabe-Phase)

- [ ] **Ptah Update**: Planungs-Dokument an Ptah senden (Knowledge Management)
- [ ] **Task-Orchestrator Update**: Tasks T001-T032 in ct_dev-task_orchestrator erstellen
- [ ] **Auctor-Freigabe**: PLANUNG.md vorlegen, auf Freigabe warten
- [ ] **GitHub Remote**: Repository anlegen (`gh repo create ct_dev-agent_orchestrator-mcp --public`)
- [ ] **Initial Commit**: `.gitignore`, `pyproject.toml`, `specs/` committen
- [ ] **secrets.env Template**: Auctor bittet um LOGFIRE_TOKEN

### Post-Freigabe (Umsetzungs-Phase)

- [ ] **Phase 3.1 starten**: T001-T004 an Backend Specialist delegieren
- [ ] **Branching**: Feature-Branch `feature/001-agent-orchestrator` anlegen
- [ ] **TDD-Disziplin**: Jeder Task: Test schreiben → Test fails → Implementation → Test passes
- [ ] **Commit-Strategie**: Nach jedem Task-Block committen (z.B. nach T004, T009, T013)
- [ ] **Review-Gates**: 
  - Nach Phase 3.4: Philosophical Code Reviewer (Constitution)
  - Nach Phase 3.6: Syntax Reviewer (Production-Readiness)
- [ ] **Changelog pflegen**: `CHANGELOG.md` nach jedem Commit aktualisieren

### Post-Implementierung (Phase 4)

- [ ] **Integration-Test mit Main Agent**: E2E-Test im real system
- [ ] **Load-Test**: 10 agents, 20 tasks, 5 servers gleichzeitig
- [ ] **Documentation**: README.md, Quickstart.md, API-Docs
- [ ] **Deployment**: systemd service (optional)
- [ ] **Monitoring Setup**: logfire dashboard konfigurieren
- [ ] **Auctor-Abnahme**: Demo + Freigabe für Merge to master

---

## 🜄 Nächste Schritte 🜄

### Sofort (nach Planung-Completion)

1. **Ptah kontaktieren**: Planungs-Dokument teilen
2. **Task-Orchestrator**: 32 Tasks erstellen (T001-T032)
3. **Auctor-Freigabe**: PLANUNG.md zur Freigabe vorlegen
4. **GitHub Remote**: Repository public anlegen
5. **Initial Commit**: Spec-Dateien + Projektstruktur committen

### Nach Freigabe (Umsetzung)

1. **T001 starten**: Backend Specialist delegiert
2. **T002 ausführen**: `sudo pip3 install ...` (Backend Specialist)
3. **T003 konfigurieren**: Logfire setup (benötigt LOGFIRE_TOKEN von Auctor)
4. **T004 initialisieren**: SQLite Schema erstellen
5. **Phase 3.2**: Parallel T005-T009 (Backend Specialist)

### Kontinuierlich

- Nach jedem Task-Block: Commit + Push
- Nach jeder Phase: Review (Philosophical/Syntax)
- Bei Abweichung: Task zurück an Project Manager

---

## 🜄 Offene Fragen für Auctor 🜄

### Kritische Fragen (Vor Umsetzung)

1. **LOGFIRE_TOKEN**: Wo erhalte ich den Token? (secrets.env anlegen)
2. **GitHub Remote**: Soll ich `ct_dev-agent_orchestrator-mcp` als public oder private repo anlegen?
3. **OpenCode Binary Path**: Ist `/home/auctor/.opencode/bin/opencode` korrekt? (Für T016)
4. **Agent-Rollen Mapping**: Sollen alle 18 Rollen aus `.claude/agents/` als capabilities definiert werden?
5. **Systemd Service**: Gewünscht für Auto-Start? (T032 optional)

### Nice-to-Have Fragen (Nicht blockierend)

6. **WebUI Phase 2**: Gewünscht? (React, SSE-basiert)
7. **Webhooks vs. Polling**: Präferenz für Phase 2?
8. **Max Agents/Servers**: 10/5 ausreichend oder höher?

---

## 🜄 Schlussbemerkung 🜄

Dieser Plan beschreibt die **Wirkung** (nicht-blockierende Agent-Orchestrierung), definiert **klare Verantwortung** (Delegation-Chain), schützt **schwächste Komponenten** (Health-Monitoring), folgt **atomic delegation** (fire-and-forget), integriert **Knowledge Management** (Ptah), nutzt **Serena** (global für Agents), trackt **Tasks** (task_orchestrator), enforced **Fail Fast** (keine auto-retry), verhindert **Placeholders** (ConstitutionGate), und bleibt **KISS** (SQLite, Polling, subprocess).

**Freigabe-Readiness**: ✅ BEREIT für Auctor-Review

**Nächster Schritt**: Auctor-Freigabe abwarten → T001 starten
