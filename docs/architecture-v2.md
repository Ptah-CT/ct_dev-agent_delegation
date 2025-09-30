# Agent Orchestrator Architecture V2

## 🎯 Zielbild: Klare Delegation und Verantwortlichkeiten

```
┌─────────────────────────────────────────────────────────────┐
│                      PM Agent (Claude)                       │
│  - Projektmanagement und Koordination                       │
│  - Nutzt Agent Orchestrator MCP Tools                       │
└────────────────┬────────────────────────────────────────────┘
                 │ MCP Protocol
                 │ Tools: spawn_agent, query_session,
                 │        control_agent, list_sessions
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Orchestrator MCP Server                   │
│  - Spawnt und managed OpenCode Server Instanzen             │
│  - Nutzt OpenCode OpenAPI für alle Operationen              │
│  - Exponiert vereinfachte MCP Tools für PM Agent            │
│  - Session Management und Lifecycle Control                 │
└────────────────┬────────────────────────────────────────────┘
                 │ OpenCode OpenAPI
                 │ GET /agent, POST /session, GET /model
                 │ POST /session/{id}/message, etc.
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                 OpenCode Server Instanzen                    │
│  (opencode serve --port 8000, 8001, 8002, ...)             │
│                                                              │
│  Pro Instanz:                                               │
│  - OpenAPI Endpoints für Agent/Model/Session Management     │
│  - Agent-Definition (aus ~/.claude/agents/)                 │
│  - Model-Selection (aus opencode models)                    │
│  - Session-basierte Kommunikation                           │
│  - MCP Tools für den Agent (von OpenCode bereitgestellt)   │
└────────────────┬────────────────────────────────────────────┘
                 │ OpenCode stellt MCP Tools bereit
                 │ (z.B. Serena, task_orchestrator, Ptah)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Specialized Agents (im OpenCode)                │
│  - backend_specialist                                        │
│  - system_architect                                         │
│  - code_analyzer                                            │
│  - etc.                                                     │
│                                                              │
│  Jeder Agent nutzt:                                         │
│  - MCP Tools von OpenCode (Serena, task_orchestrator, etc) │
│  - Model (konfiguriert via OpenCode API)                   │
│  - Custom Instructions (aus ~/.claude/agents/*.md)          │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Schlüssel-Konzepte

### 1. PM Agent (Project Manager Agent)
**Rolle**: Orchestrierung und Koordination auf höchster Ebene

**Nutzt MCP Tools von Agent Orchestrator**:
- `spawn_agent(role, task_context)` - Startet neuen Specialized Agent
- `query_session(session_id)` - Holt aktuellen Status aus OpenCode Session
- `send_to_agent(session_id, message)` - Sendet Nachricht an Agent
- `list_active_sessions()` - Zeigt alle laufenden Agent-Sessions
- `stop_agent(session_id)` - Beendet Agent-Session
- `get_agent_output(session_id)` - Holt bisherige Outputs

**Verantwortlichkeiten**:
- Entscheidet WANN welcher Agent gebraucht wird
- Formuliert klare Arbeitsaufträge
- Pollt Status und Zwischenergebnisse
- Entscheidet über Weiterleitung oder Abbruch

### 2. Agent Orchestrator MCP Server
**Rolle**: OpenCode Instance Lifecycle Management

**Nutzt OpenCode OpenAPI**:
```
GET  /agent                    -> Liste verfügbarer Agents
GET  /model                    -> Liste verfügbarer Models
POST /session                  -> Session erstellen
  {
    "agent": "backend-specialist",
    "model": "claude-sonnet-4",
    "directory": "/path/to/project"
  }
POST /session/{id}/message     -> Nachricht an Agent senden
GET  /session/{id}/history     -> Session-Historie abrufen
DELETE /session/{id}           -> Session beenden
```

**Bietet MCP Tools an**:
- Vereinfachte, PM-Agent-freundliche API
- Session-basierte Abstraktion (kein direkter Port-Management)
- Health Monitoring der OpenCode Instanzen
- Automatisches Cleanup bei Crashes

**Verantwortlichkeiten**:
- Spawnen von `opencode serve` Prozessen (verschiedene Ports)
- Health Checks der Prozesse (psutil)
- API-Forwarding an OpenCode Sessions
- Session Lifecycle Management

### 3. OpenCode Server Instanzen
**Rolle**: Agent Runtime mit vollständigem Feature-Set

**Bietet OpenAPI an**:
- Agent Management (dynamisch aus ~/.claude/agents/)
- Model Selection (dynamisch aus opencode models)
- Session Management (stateful conversations)
- Message Routing (zu Agents)

**Bietet MCP Tools für Agents an**:
- Serena (Code Operations)
- task_orchestrator (Task Management)
- Ptah (Knowledge Management)
- GitHub, Infisical, etc. (je nach Konfiguration)

**Verantwortlichkeiten**:
- Agent Execution (mit Custom Instructions)
- Tool-Aufruf-Verwaltung
- Context Management
- Model Interaction

### 4. Specialized Agents (innerhalb OpenCode)
**Rolle**: Spezialisierte Fachexperten

**Haben Zugriff auf**:
- Alle MCP Tools von OpenCode
- Custom Instructions aus ~/.claude/agents/*.md
- Konfiguriertes Model
- Session Context

**Verantwortlichkeiten**:
- Spezialisierte Aufgaben ausführen
- MCP Tools nutzen für Code/Tasks/Knowledge
- Ergebnisse zurückliefern
- Scope-Einhaltung

## 🔄 Beispiel-Flow: Backend Implementation Task

### Schritt 1: PM Agent entscheidet
```
PM Agent Gedanke:
"Ich brauche einen Backend Specialist für die OAuth Implementation.
Task ist definiert in task_orchestrator."

PM Agent ruft MCP Tool:
spawn_agent(
  role="backend_specialist",
  task_id="550e8400-...",
  instructions="Implement OAuth2 endpoints per task specification",
  context={
    "framework": "FastAPI",
    "task_orchestrator_task_id": "550e8400-..."
  }
)
```

### Schritt 2: Agent Orchestrator spawnt OpenCode
```python
# Agent Orchestrator empfängt spawn_agent Request
async def spawn_agent(role, task_id, instructions, context):
    # 1. Port auswählen
    port = get_next_available_port()  # z.B. 8001
    
    # 2. OpenCode Server starten
    subprocess.Popen([
        "opencode", "serve",
        "--port", str(port),
        "--agent", role,  # OpenCode lädt ~/.claude/agents/{role}.md
        "--model", "claude-sonnet-4"
    ])
    
    # 3. Warten bis healthy
    await wait_for_health(f"http://localhost:{port}/health")
    
    # 4. Session erstellen via OpenCode API
    session = await create_session(
        server_url=f"http://localhost:{port}",
        agent=role,
        directory=context.get("project_path")
    )
    
    # 5. Initial Message senden
    await send_message(
        server_url=f"http://localhost:{port}",
        session_id=session["id"],
        message=instructions,
        context=context
    )
    
    return {
        "session_id": session["id"],
        "server_url": f"http://localhost:{port}",
        "status": "running"
    }
```

### Schritt 3: OpenCode führt Agent aus
```
OpenCode Server (Port 8001):
1. Lädt Agent Definition: ~/.claude/agents/backend_specialist.md
2. Initialisiert Model: claude-sonnet-4
3. Erstellt Session mit Context
4. Empfängt Message: "Implement OAuth2 endpoints..."
5. Agent beginnt Arbeit:
   - Nutzt task_orchestrator MCP Tool (von OpenCode bereitgestellt)
   - Nutzt Serena MCP Tool für Code Operations
   - Nutzt GitHub MCP Tool für Repository Access
6. Agent produziert Output
```

### Schritt 4: PM Agent pollt Zwischenstand
```
PM Agent ruft periodisch:
status = query_session(session_id="abc-123")

Response:
{
  "session_id": "abc-123",
  "status": "running",
  "progress": {
    "current_step": "Implementing OAuth endpoints",
    "completed_steps": ["Analyzed requirements", "Created models"],
    "pending_steps": ["Add tests", "Update documentation"]
  },
  "messages": [
    {"role": "user", "content": "Implement OAuth2..."},
    {"role": "assistant", "content": "I'll implement OAuth2. First..."},
    {"role": "assistant", "content": "Created models in models/auth.py..."}
  ]
}
```

### Schritt 5: PM Agent holt Ergebnis
```
PM Agent:
output = get_agent_output(session_id="abc-123")

Response:
{
  "session_id": "abc-123",
  "status": "completed",
  "artifacts": {
    "files_created": ["models/auth.py", "api/auth.py", "tests/test_auth.py"],
    "files_modified": ["api/__init__.py"],
    "task_updated": true
  },
  "summary": "Successfully implemented OAuth2 authentication...",
  "duration_seconds": 450
}
```

## 🎨 MCP Tool Design für Agent Orchestrator

### Tool 1: spawn_agent
```python
@mcp.tool()
async def spawn_agent(
    role: str,  # "backend_specialist", "system_architect", etc.
    task_id: str,  # Task UUID from task_orchestrator
    instructions: str,  # Detailed work instructions
    context: dict = {},  # Additional context
    model: str = "claude-sonnet-4"  # Model to use
) -> dict:
    """
    Spawns a new OpenCode server instance with specified agent.
    Returns immediately with session_id for tracking.
    
    Returns:
        {
            "session_id": "uuid",
            "server_url": "http://localhost:8001",
            "status": "running",
            "agent_role": "backend_specialist",
            "model": "claude-sonnet-4"
        }
    """
```

### Tool 2: query_session
```python
@mcp.tool()
async def query_session(session_id: str) -> dict:
    """
    Queries current status of an agent session.
    Non-blocking, returns current state from OpenCode API.
    
    Returns:
        {
            "session_id": "uuid",
            "status": "running" | "completed" | "failed",
            "progress": {...},
            "messages": [...],
            "artifacts": {...}
        }
    """
```

### Tool 3: send_to_agent
```python
@mcp.tool()
async def send_to_agent(
    session_id: str,
    message: str
) -> dict:
    """
    Sends additional message to running agent session.
    Useful for clarifications, adjustments, or follow-up tasks.
    
    Returns:
        {
            "success": true,
            "message_sent": "...",
            "timestamp": "2024-09-30T..."
        }
    """
```

### Tool 4: list_active_sessions
```python
@mcp.tool()
async def list_active_sessions() -> list:
    """
    Lists all currently active agent sessions.
    
    Returns:
        [
            {
                "session_id": "uuid",
                "agent_role": "backend_specialist",
                "status": "running",
                "started_at": "2024-09-30T...",
                "task_id": "..."
            },
            ...
        ]
    """
```

### Tool 5: stop_agent
```python
@mcp.tool()
async def stop_agent(session_id: str) -> dict:
    """
    Stops an agent session and cleans up resources.
    
    Returns:
        {
            "success": true,
            "session_id": "uuid",
            "final_status": "cancelled" | "completed"
        }
    """
```

### Tool 6: get_agent_capabilities
```python
@mcp.tool()
async def get_agent_capabilities(role: str) -> dict:
    """
    Returns capabilities and description of an agent role.
    Fetched dynamically from OpenCode /agent endpoint.
    
    Returns:
        {
            "role": "backend_specialist",
            "description": "...",
            "tools_available": ["serena", "task_orchestrator", ...],
            "suitable_for": ["API development", "Database design", ...]
        }
    """
```

## 🔧 Implementation-Prioritäten

### Phase 1: Core Session Management (AKTUELL)
- ✅ OpenCode API Client (opencode_api_client.py) 
- ✅ Session Manager (session_manager.py)
- 🔄 MCP Tools umbenennen/umbauen:
  - `delegate_work` → `spawn_agent`
  - `get_delegation_status` → `query_session`
  - `get_delegation_result` → `get_agent_output`
  - Neue: `send_to_agent`, `list_active_sessions`

### Phase 2: OpenCode API Integration
- 🔄 Dynamische Agent Discovery (GET /agent)
- 🔄 Dynamische Model Selection (GET /model)
- 🔄 Session-based Communication (POST /session/{id}/message)
- 🔄 Session History Retrieval (GET /session/{id}/history)

### Phase 3: PM Agent Experience
- ⏳ Vereinfachte MCP Tool API
- ⏳ Progress Tracking und Polling
- ⏳ Error Handling und Recovery
- ⏳ Session Cleanup und Lifecycle

### Phase 4: Production Features
- ⏳ Multi-Session Management
- ⏳ Load Balancing (Port Pool)
- ⏳ Health Monitoring
- ⏳ Persistence zwischen Restarts

## 🎯 Key Differences zur bisherigen Planung

### Alt (Delegation-basiert)
```
PM Agent → delegate_work(task) → Agent Manager creates Agent
                                 ↓
                            OpenCode starts
                                 ↓
                            Agent executes
                                 ↓
                            Returns result
```

### Neu (Session-basiert)
```
PM Agent → spawn_agent(role) → Agent Orchestrator spawns OpenCode
                                 ↓
                            OpenCode creates Session
                                 ↓
PM Agent → query_session() → Gets current state
                                 ↓
PM Agent → send_to_agent() → Sends follow-up
                                 ↓
PM Agent → get_agent_output() → Gets final result
```

## 💡 Vorteile des neuen Designs

1. **Klarere Verantwortlichkeiten**:
   - PM Agent: WANN und WAS
   - Agent Orchestrator: WIE (Lifecycle)
   - OpenCode: Execution Runtime
   - Agents: Spezialisierte Tasks

2. **OpenCode as Single Source of Truth**:
   - Alle Agent-Definitionen in OpenCode
   - Alle Models von OpenCode
   - Alle Tools für Agents von OpenCode
   - Keine Duplikation

3. **Session-basierte Interaktion**:
   - PM Agent kann während Execution kommunizieren
   - Zwischenstände abrufbar
   - Flexible Steuerung (pause, resume, adjust)

4. **Skalierbarkeit**:
   - Multiple OpenCode Instanzen parallel
   - Port-Pool Management
   - Load Balancing möglich

5. **Testbarkeit**:
   - OpenCode API mockbar
   - Session-Logik isoliert testbar
   - PM Agent unabhängig testbar

---

**Status**: Architektur V2 definiert, Ready for Implementation
**Next**: Refactoring der aktuellen Implementation auf Session-basiertes Model
