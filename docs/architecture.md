# Agent Orchestrator Architecture

## Zielbild

```
PM Agent 
  ↓ (MCP Client)
Agent Orchestrator (MCP Server)
  ↓ (HTTP/OpenAPI)
OpenCode Server Instance(s)
  ↓ (Native MCP Integration)
Agents + MCP Tools
```

## Komponenten

### 1. PM Agent (Project Manager Agent)
**Rolle**: Koordiniert Projektarbeit über MCP Tools

**Verwendet**:
- Agent Orchestrator MCP Tools (client)
- Spawnt Agents für spezifische Aufgaben
- Ruft Zwischenstände aus OpenCode Sessions ab
- Steuert Agent-Lifecycle

**Beispiel-Tools** (vom Agent Orchestrator bereitgestellt):
- `spawn_agent(agent_name, task, context)`
- `get_session_status(session_id)`
- `get_session_messages(session_id)`
- `abort_session(session_id)`
- `list_active_agents()`

### 2. Agent Orchestrator (MCP Server)
**Rolle**: MCP Server der OpenCode-Instanzen managed

**Verantwortlichkeiten**:
- Spawnt `opencode serve` Instanzen (subprocess)
- Nutzt OpenCode Server API (HTTP/OpenAPI) für alle Operationen
- Übersetzt zwischen MCP Tools (für PM Agent) und OpenCode API
- Session Management über OpenCode API
- Health Monitoring der Instanzen
- Load Balancing über mehrere Instanzen

**Bietet MCP Tools für**:
- Agent/Session Lifecycle
- Session-Status-Abfragen
- Message Retrieval
- Agent Configuration (dynamisch aus OpenCode)

**Nutzt OpenCode API**:
- `GET /agent` - Available agents
- `POST /session` - Create session
- `GET /session/{id}` - Get session status
- `POST /session/{id}/message` - Send message
- `GET /session/{id}/message` - Get messages
- `POST /session/{id}/abort` - Abort session
- `DELETE /session/{id}` - Delete session
- `GET /config` - Get configuration
- `PATCH /config` - Update configuration

### 3. OpenCode Server (opencode serve)
**Rolle**: Agent Runtime mit API

**Bietet**:
- RESTful API (OpenAPI 3.1.1)
- Agent Definitions (GET /agent)
- Model Management
- Session Management (vollständig)
- File Operations
- Command Execution
- Native MCP Tool Integration für Agents

**Sessions**:
- Jede Session = ein Agent-Task
- Zustandsbehaftet (Messages, Files, Permissions)
- Kann aborted, reverted, summarized werden
- Hat Children (Sub-Sessions)

**Agents haben Zugriff auf**:
- MCP Tools (z.B. Ptah, Serena, GitHub, etc.)
- File System (kontrolliert)
- Shell Commands (kontrolliert)
- Permissions System

### 4. Agents (in OpenCode)
**Rolle**: Spezialisierte Agenten für Tasks

**Eigenschaften**:
- Definiert in OpenCode Config
- Built-in oder Custom
- Haben Tools, Permissions, Options
- Nutzen MCP Tools direkt (nativ in OpenCode)

**Beispiele**:
- `general` - General-purpose
- `build` - Build tasks
- `plan` - Planning
- `philosophical-code-reviewer` - Code review
- Custom agents (dynamisch definierbar)

## Datenfluss

### Agent Spawning
```
1. PM Agent: spawn_agent("backend-specialist", "Implement API", context)
2. Agent Orchestrator:
   - Wählt/startet OpenCode Instance
   - POST /session (create session mit agent="backend-specialist")
   - Speichert Session-ID + Metadata
   - Returniert session_id
3. OpenCode:
   - Startet Session mit Agent "backend-specialist"
   - Agent hat Zugriff auf MCP Tools (Ptah, Serena, etc.)
4. PM Agent: Erhält session_id
```

### Status Abfrage
```
1. PM Agent: get_session_status(session_id)
2. Agent Orchestrator:
   - GET /session/{session_id}
   - Parsed Response
3. OpenCode: Returns Session Object (status, messages, etc.)
4. PM Agent: Erhält Status (idle/running/error/aborted)
```

### Message Retrieval
```
1. PM Agent: get_session_messages(session_id)
2. Agent Orchestrator:
   - GET /session/{session_id}/message
3. OpenCode: Returns Messages Array
4. PM Agent: Erhält alle Messages mit Parts (text, files, patches, etc.)
```

### Task Submission
```
1. PM Agent: send_message(session_id, "Implement the feature")
2. Agent Orchestrator:
   - POST /session/{session_id}/message
   - Body: {message: "Implement the feature"}
3. OpenCode:
   - Agent verarbeitet Message
   - Nutzt MCP Tools (Serena für Code, Ptah für Knowledge, etc.)
   - Schreibt Code, Updated Files
   - Returniert Response
4. PM Agent: Erhält Response (via get_session_messages)
```

## API Mapping

### MCP Tools → OpenCode API

| MCP Tool (PM Agent) | OpenCode API Endpoint | Beschreibung |
|---------------------|----------------------|--------------|
| `spawn_agent` | `POST /session` | Create new agent session |
| `get_session_status` | `GET /session/{id}` | Get session details |
| `get_session_messages` | `GET /session/{id}/message` | Get all messages |
| `send_message` | `POST /session/{id}/message` | Send prompt to agent |
| `abort_session` | `POST /session/{id}/abort` | Abort running session |
| `delete_session` | `DELETE /session/{id}` | Delete session |
| `list_sessions` | `GET /session` | List all sessions |
| `list_agents` | `GET /agent` | Get available agents |
| `get_config` | `GET /config` | Get OpenCode config |
| `update_config` | `PATCH /config` | Update config |

## Implementierungsschritte

### Phase 1: OpenCode API Integration ✓
- [x] OpenCode API Schema dokumentieren (docs/opencode-api-schema.json)
- [x] API Client implementieren (services/opencode_api_client.py)
- [x] Session Manager implementieren (services/session_manager.py)
- [ ] Agent Discovery über API (GET /agent)
- [ ] Model Discovery über API (GET /config/providers)

### Phase 2: MCP Server Implementation
- [ ] MCP Tools definieren
  - [ ] `spawn_agent` - Create session
  - [ ] `get_session_status` - Get session details
  - [ ] `get_session_messages` - Get messages
  - [ ] `send_message` - Send prompt
  - [ ] `abort_session` - Abort session
  - [ ] `delete_session` - Delete session
  - [ ] `list_sessions` - List all sessions
  - [ ] `list_agents` - Get available agents
- [ ] Tool Implementation (tools/)
- [ ] Error Handling mit Context
- [ ] Health Monitoring Background Task

### Phase 3: Multi-Instance Management
- [ ] OpenCode Server Pool Manager
  - [ ] Port Management (base_port + offset)
  - [ ] Process Lifecycle (subprocess start/stop)
  - [ ] Health Check Loop
  - [ ] Auto-Restart bei Failure
- [ ] Load Balancing
  - [ ] Round-Robin Session Distribution
  - [ ] Instance Selection Logic
- [ ] Failover Strategy
  - [ ] Session Migration bei Server Failure
  - [ ] Graceful Degradation

### Phase 4: Testing & Integration
- [ ] Unit Tests
  - [ ] API Client Tests (Mock HTTP)
  - [ ] Session Manager Tests
  - [ ] Load Balancer Tests
- [ ] Integration Tests
  - [ ] Real OpenCode Server Tests
  - [ ] Multi-Instance Tests
- [ ] MCP Tool Tests
  - [ ] Tool Call Tests
  - [ ] Error Scenarios
- [ ] End-to-End Tests
  - [ ] PM Agent Simulation → Orchestrator → OpenCode

### Phase 5: Documentation & Polish
- [ ] MCP Tool Documentation
- [ ] API Examples
- [ ] Configuration Guide
- [ ] Troubleshooting Guide

## Wichtige Designentscheidungen

### ✓ Validierte Architekturentscheidungen

1. **API-First Approach** ✓
   - Agent Orchestrator greift NICHT auf `.claude/agents/` File-System zu
   - Alle Informationen (Agents, Models, Config) dynamisch von OpenCode API
   - **Rationale**: OpenCode ist Single Source of Truth, vermeidet Sync-Probleme

2. **Session = Agent Instance** ✓
   - Jede OpenCode Session ist ein laufender Agent-Task
   - Session-ID wird direkt zum PM Agent durchgereicht
   - Keine zusätzliche Abstraktionsschicht
   - **Rationale**: OpenCode Sessions sind dafür designed, haben bereits State/Messages/Children

3. **Multi-Instance Strategy** ✓
   - Mehrere `opencode serve` Prozesse parallel
   - Port-basiertes Load Balancing
   - Konfigurierbar: 5-10 max concurrent agents
   - **Rationale**: Echte Parallelität, Isolation, bessere Resource-Nutzung

4. **Minimal State Caching** ✓
   - Orchestrator cached nur Session-ID ↔ Server-URL Mapping
   - Alle anderen Daten live von OpenCode API
   - **Rationale**: Immer aktuell, keine Sync-Probleme, einfacher zu maintainen

5. **Transparente Error Propagation** ✓
   - OpenCode Errors werden durchgereicht mit Kontext
   - Keine Error-Abstraktion oder Mapping
   - **Rationale**: Volle Information für PM Agent, kein Information Loss

6. **Fail-Fast Philosophy** ✓
   - Bei OpenCode Problemen schnell fehlschlagen
   - Keine endlosen Retries (max 2-3)
   - Health Checks mit schnellem Timeout
   - **Rationale**: PM Agent kann besser auf Fehler reagieren als der Orchestrator

## Sicherheit & Permissions

OpenCode hat eingebautes Permission System:
- `edit`: allow/deny file editing
- `webfetch`: allow/deny web access
- `bash`: Granular command permissions

Agent Orchestrator übernimmt diese Permissions aus OpenCode API und kann sie nicht überschreiben.

## Performance Considerations

- **OpenCode Startup**: 2-5 Sekunden pro Instance
- **Memory**: ~200-500MB pro OpenCode Instance
- **CPU**: ~10-20% pro aktive Session
- **Max Agents**: 5-10 concurrent (configurable)
- **Session Pooling**: Wiederverwendung von idle Sessions möglich

## Error Handling

1. **OpenCode Server Down**: Health Check failed → Restart
2. **Session Error**: Returned in Session Status → Report to PM Agent
3. **API Timeout**: Configurable Timeout → Abort & Report
4. **Permission Denied**: OpenCode Permission System → Forward to PM Agent
5. **Resource Exhausted**: Max Agents erreicht → Queue oder Reject

## Monitoring & Observability

Via Logfire:
- Session Creation/Deletion
- API Call Latency
- Error Rates
- Active Sessions Count
- Resource Usage (CPU, Memory)
- Agent Performance Metrics
