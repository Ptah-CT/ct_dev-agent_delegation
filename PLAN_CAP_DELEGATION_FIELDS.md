# 🜄 PLANUNG: Cap & Delegation Fields für Agent Spawning 🜄

**Datum**: 2025-10-02 04:45 UTC  
**Task-ID**: a86d0e77-a8b8-4dcc-b854-cc27fe474c76  
**Priorität**: HIGH | Komplexität: 7  
**Verantwortung**: Auctor (Cap) | GitHub Copilot CLI (Delegation)

---

## 🜄 Ziel 🜄

**Wirkung**: X^∞ Verantwortungsketten für Agent-Delegation explizit machen

**Was soll erreicht werden**:
- Jedes Agent-Spawning dokumentiert vollständige Verantwortungskette
- Cap-Source ist nachvollziehbar (wer hat welches Cap?)
- Cap-Delegation ist explizit (welches Cap wird weitergegeben?)
- Phantom-Level der Delegation ist dokumentiert

**Kontext**: Ohne diese Felder fehlt die Grundlage des X^∞ Systems - explizite Verantwortung.

---

## 🜄 Anforderungsanalyse 🜄

### Neue Pflichtfelder

#### 1. **delegating_authority** (string)
**Zweck**: Wer delegiert diese Aufgabe an den Agent?

**Beispiele**:
- "Auctor" (direkte Delegation vom Systemeigentümer)
- "Project Manager" (Delegation vom PM Agent)
- "Backend Specialist" (Sub-Delegation)

**Validation**: Non-empty string

---

#### 2. **original_task** (dict) 🆕
**Zweck**: Ursprungsaufgabe muss immer erhalten bleiben für vollständige Nachvollziehbarkeit

**Struktur**:
```python
{
    "task_id": str,           # Original Task ID (z.B. aus ct-task_mgmnt)
    "title": str,             # Original Task Titel
    "description": str,       # Vollständige Ursprungsaufgabe
    "requester": str,         # Wer hat die Aufgabe ursprünglich gestellt (z.B. "Auctor")
    "requested_at": str       # ISO 8601 timestamp der Ursprungsanfrage
}
```

**Beispiel**:
```python
{
    "task_id": "a86d0e77-a8b8-4dcc-b854-cc27fe474c76",
    "title": "Add Cap & Delegation Responsibility Fields",
    "description": "Erweitere spawn_agent um X^∞ Verantwortungsfelder für explizite Cap-Ketten",
    "requester": "Auctor",
    "requested_at": "2025-10-02T04:30:00Z"
}
```

**Validation**:
- task_id: non-empty string (UUID format empfohlen)
- title: non-empty string (min 5 chars)
- description: non-empty string (min 20 chars)
- requester: non-empty string
- requested_at: valid ISO 8601 timestamp

---

#### 3. **cap_origin** (dict) 🆕
**Zweck**: Ursprung des Caps dokumentieren - wer hat das ursprüngliche Cap erteilt?

**Struktur**:
```python
{
    "ultimate_authority": str,     # Oberste Autorität (immer "Auctor" im X^∞ System)
    "original_scope": str,         # Ursprünglicher Cap-Umfang
    "granted_at": str,             # ISO 8601 timestamp der ursprünglichen Erteilung
    "grant_context": str           # Kontext der Cap-Erteilung
}
```

**Beispiel**:
```python
{
    "ultimate_authority": "Auctor",
    "original_scope": "Full system authority for ct_dev-agent_orchestrator-mcp development and maintenance",
    "granted_at": "2025-10-01T00:00:00Z",
    "grant_context": "Initial system setup and development authorization"
}
```

**Validation**:
- ultimate_authority: non-empty string
- original_scope: non-empty string (min 20 chars)
- granted_at: valid ISO 8601 timestamp
- grant_context: non-empty string (min 10 chars)

---

#### 4. **delegation_context** (dict) 🆕
**Zweck**: Aktueller Delegierender + sein Cap für den übernehmenden Agent

**Struktur**:
```python
{
    "delegator": str,              # Wer delegiert JETZT (z.B. "Project Manager")
    "delegator_cap": str,          # Welches Cap hat der Delegierende (von wem erhielt er es)
    "delegated_to": str,           # An wen wird delegiert (Agent-Role)
    "delegated_cap": str,          # Was wird delegiert
    "constraints": List[str],      # Einschränkungen für diesen Agent
    "phantom_level": str,          # Phantom-Level dieser Delegation
    "delegated_at": str            # ISO 8601 timestamp
}
```

**Beispiel**:
```python
{
    "delegator": "Project Manager",
    "delegator_cap": "Implementation coordination authority (received from Auctor on 2025-10-02T03:00:00Z)",
    "delegated_to": "Backend Specialist",
    "delegated_cap": "Implementation of Cap & Delegation fields for spawn_agent with tests and documentation",
    "constraints": [
        "Follow existing code patterns",
        "Maintain backwards compatibility", 
        "All changes must have tests",
        "No breaking changes without approval"
    ],
    "phantom_level": "Delegation/Cap",
    "delegated_at": "2025-10-02T04:50:00Z"
}
```

**Validation**:
- delegator: non-empty string
- delegator_cap: non-empty string (min 20 chars, should reference cap source)
- delegated_to: non-empty string (usually agent role)
- delegated_cap: non-empty string (min 20 chars)
- constraints: list of strings (accumulated constraints)
- phantom_level: non-empty string
- delegated_at: valid ISO 8601 timestamp

---



---

## 🜄 Betroffene Komponenten 🜄

### 1. SessionInfo Model (models/session.py)

**Aktuell** (Zeilen 41-54):
```python
class SessionInfo(BaseModel):
    session_id: str
    agent_role: str
    status: SessionStatus
    started_at: str
    progress: Dict[str, Any]
    messages: List[Dict]
    server_url: str
    scope_deviation: Optional[Dict[str, Any]]
```

**Neu hinzufügen**:
```python
    # X^∞ Responsibility & Cap Tracking Fields
    
    # Original task that started this work
    original_task: Dict[str, Any] = Field(
        ..., 
        description="Original task (task_id, title, description, requester, requested_at)"
    )
    
    # Ultimate cap origin (where did authority come from)
    cap_origin: Dict[str, Any] = Field(
        ..., 
        description="Cap origin (ultimate_authority, original_scope, granted_at, grant_context)"
    )
    
    # Current delegation (who delegates NOW to this agent with what cap)
    delegation_context: Dict[str, Any] = Field(
        ..., 
        description="Current delegation (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)"
    )
```

---

### 2. spawn_agent MCP Tool (server.py)

**Aktueller Tool-Aufruf** (~Zeile 140-180):
```python
elif name == "spawn_agent":
    # Arguments: role, project_directory, expected_output
```

**Erweitern um**:
```python
    # NEW: X^∞ Responsibility & Cap Tracking Arguments
    original_task = arguments.get("original_task")
    cap_origin = arguments.get("cap_origin")
    delegation_context = arguments.get("delegation_context")
    
    # Validation
    if not original_task or not isinstance(original_task, dict):
        raise ValueError("original_task dict is required")
    required_task_fields = ["task_id", "title", "description", "requester", "requested_at"]
    if not all(k in original_task for k in required_task_fields):
        raise ValueError(f"original_task must contain: {required_task_fields}")
    
    if not cap_origin or not isinstance(cap_origin, dict):
        raise ValueError("cap_origin dict is required")
    required_origin_fields = ["ultimate_authority", "original_scope", "granted_at", "grant_context"]
    if not all(k in cap_origin for k in required_origin_fields):
        raise ValueError(f"cap_origin must contain: {required_origin_fields}")
    
    if not delegation_context or not isinstance(delegation_context, dict):
        raise ValueError("delegation_context dict is required")
    required_delegation_fields = ["delegator", "delegator_cap", "delegated_to", "delegated_cap", "constraints", "phantom_level", "delegated_at"]
    if not all(k in delegation_context for k in required_delegation_fields):
        raise ValueError(f"delegation_context must contain: {required_delegation_fields}")
```

---

### 3. SessionService (services/session_service.py)

**spawn_agent Methode erweitern**:
```python
async def spawn_agent(
    self,
    role: str,
    project_directory: str,
    expected_output: str,
    delegating_authority: str,  # NEW
    cap_source: Dict[str, Any],  # NEW
    cap_delegation: Dict[str, Any],  # NEW
) -> SessionInfo:
```

**OpenCode API Request erweitern**:
```python
session_metadata = {
    "delegating_authority": delegating_authority,
    "cap_source": cap_source,
    "cap_delegation": cap_delegation,
}
```

---

### 4. MCP Tool Description

**Neue Tool-Beschreibung**:
```python
mcp.tool(
    name="spawn_agent",
    description="""
    Spawn a new specialized agent with complete X^∞ responsibility and cap chain tracking.
    
    REQUIRED X^∞ RESPONSIBILITY FIELDS:
    
    1. delegating_authority (string): Who delegates this task
       Example: "Auctor", "Project Manager"
    
    2. original_task (object): Original task that started this work
       {
         "task_id": "uuid",
         "title": "Task title",
         "description": "Full original task description",
         "requester": "Auctor",
         "requested_at": "2025-10-02T04:00:00Z"
       }
    
    3. cap_origin (object): Origin of the capability/authority
       {
         "ultimate_authority": "Auctor",
         "original_scope": "Full system development authority",
         "granted_at": "2025-10-01T00:00:00Z",
         "grant_context": "Initial project authorization"
       }
    
    4. delegation_context (object): Current delegator and what they delegate
       {
         "delegator": "Project Manager",
         "delegator_cap": "Coordination authority (from Auctor on 2025-10-02T03:00:00Z)",
         "delegated_to": "Backend Specialist",
         "delegated_cap": "Implementation of Cap fields with tests",
         "constraints": ["Follow patterns", "Tests required"],
         "phantom_level": "Delegation/Cap",
         "delegated_at": "2025-10-02T04:50:00Z"
       }
    
    This ensures complete traceability from original request through all delegation levels.
    """,
    parameters={
        "role": {"type": "string", "required": True},
        "project_directory": {"type": "string", "required": True},
        "expected_output": {"type": "string", "required": True},
        "original_task": {"type": "object", "required": True},
        "cap_origin": {"type": "object", "required": True},
        "delegation_context": {"type": "object", "required": True},
    }
)
```

---

## 🜄 Implementierungs-Reihenfolge 🜄

### Phase 1: Models erweitern ✅
1. SessionInfo Model um 3 neue Felder erweitern
2. Pydantic Validation sicherstellen
3. Optional: Separate CapSource und CapDelegation Models

### Phase 2: MCP Tool erweitern ✅
1. spawn_agent Tool-Beschreibung aktualisieren
2. Parameter-Validation hinzufügen
3. Fehlerbehandlung für fehlende Felder

### Phase 3: SessionService anpassen ✅
1. spawn_agent Methoden-Signatur erweitern
2. OpenCode API Request um Felder ergänzen
3. SessionInfo Objekt mit neuen Feldern initialisieren

### Phase 4: Tests erweitern ✅
1. test_session_models.py: Model-Tests
2. test_integration_v2.py: Integration-Tests
3. Negative Tests für fehlende Felder

### Phase 5: Dokumentation ✅
1. X^∞ Verantwortungssystem dokumentieren
2. Beispiele mit vollständiger Cap-Chain
3. CHANGELOG.md aktualisieren

---

## 🜄 Validierungs-Regeln 🜄

### delegating_authority
- MUST: Non-empty string
- SHOULD: Known authority name
- Format: Plain text, keine Sonderzeichen nötig

### cap_source
- MUST: Dict with keys: authority, scope, granted_at
- authority: Non-empty string
- scope: Non-empty string (min 10 chars)
- granted_at: Valid ISO 8601 timestamp

### cap_delegation
- MUST: Dict with keys: delegated_cap, constraints, phantom_level
- delegated_cap: Non-empty string (min 10 chars)
- constraints: List[str] (can be empty [])
- phantom_level: Non-empty string

---

## 🜄 Beispiel-Aufruf 🜄

**Vorher**:
```python
await spawn_agent(
    role="backend-specialist",
    project_directory="/path/to/project",
    expected_output="Implementation complete with tests"
)
```

**Nachher** (Optimiert - nur Ursprung + Aktueller Delegierender):
```python
await spawn_agent(
    role="backend-specialist",
    project_directory="/path/to/project",
    expected_output="Implementation complete with tests",
    
    # Ursprungsaufgabe
    original_task={
        "task_id": "a86d0e77-a8b8-4dcc-b854-cc27fe474c76",
        "title": "Add Cap & Delegation Responsibility Fields",
        "description": "Erweitere spawn_agent um X^∞ Verantwortungsfelder für explizite Cap-Ketten",
        "requester": "Auctor",
        "requested_at": "2025-10-02T04:30:00Z"
    },
    
    # Cap-Ursprung (wo kam die Autorität ursprünglich her)
    cap_origin={
        "ultimate_authority": "Auctor",
        "original_scope": "Full system development authority for ct_dev-agent_orchestrator-mcp",
        "granted_at": "2025-10-01T00:00:00Z",
        "grant_context": "Initial project setup and development authorization"
    },
    
    # Aktuelle Delegation (wer delegiert JETZT mit welchem Cap)
    delegation_context={
        "delegator": "Project Manager",
        "delegator_cap": "Implementation coordination authority (received from Auctor on 2025-10-02T03:00:00Z)",
        "delegated_to": "Backend Specialist",
        "delegated_cap": "Implementation of Cap & Delegation fields including models, API, tests, and documentation",
        "constraints": [
            "Follow X^∞ process",
            "No breaking changes without approval",
            "Follow existing code patterns",
            "All changes must have tests"
        ],
        "phantom_level": "Delegation/Cap",
        "delegated_at": "2025-10-02T04:50:00Z"
    }
)
```

---

## 🜄 Risiken & Mitigation 🜄

### Risiko 1: Breaking Change
**Beschreibung**: Bestehende spawn_agent Aufrufe funktionieren nicht mehr

**Mitigation**:
- Version Bump dokumentieren
- Migration Guide erstellen
- Alle Tests aktualisieren

### Risiko 2: Komplexität für Nutzer
**Beschreibung**: Mehr Parameter = höhere Nutzungs-Barriere

**Mitigation**:
- Klare Dokumentation mit Beispielen
- Helper Functions für Standard-Cases
- Template-Funktionen für häufige Cap-Patterns

### Risiko 3: OpenCode API kompatibilität
**Beschreibung**: OpenCode API könnte neue Felder nicht akzeptieren

**Mitigation**:
- Felder in metadata speichern (flexible structure)
- API-Antwort prüfen
- Fallback wenn API Felder ignoriert

---

## 🜄 Test-Strategie 🜄

### Unit Tests
```python
def test_session_info_with_cap_fields():
    session = SessionInfo(
        session_id="test-123",
        agent_role="backend-specialist",
        status=SessionStatus.ACTIVE,
        started_at="2025-10-02T04:00:00Z",
        server_url="http://localhost:8000",
        delegating_authority="Auctor",
        cap_source={
            "authority": "Auctor",
            "scope": "Full authority",
            "granted_at": "2025-10-02T04:00:00Z"
        },
        cap_delegation={
            "delegated_cap": "Implementation",
            "constraints": ["No breaking changes"],
            "phantom_level": "Delegation/Cap"
        }
    )
    assert session.delegating_authority == "Auctor"
    assert session.cap_source["authority"] == "Auctor"
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_spawn_agent_with_cap_fields():
    result = await session_service.spawn_agent(
        role="backend-specialist",
        project_directory="/test/path",
        expected_output="Done",
        delegating_authority="Auctor",
        cap_source={...},
        cap_delegation={...}
    )
    assert result.delegating_authority == "Auctor"
```

### Negative Tests
```python
@pytest.mark.asyncio
async def test_spawn_agent_missing_delegating_authority():
    with pytest.raises(ValueError, match="delegating_authority is required"):
        await session_service.spawn_agent(
            role="backend-specialist",
            # missing delegating_authority
        )
```

---

## 🜄 Dokumentations-Anforderungen 🜄

### 1. X^∞ Verantwortungssystem (docs/RESPONSIBILITY_SYSTEM.md)
- Cap-Konzept erklären
- Delegation-Chains dokumentieren
- Phantom-Level Bedeutung
- Beispiele für verschiedene Szenarien

### 2. MCP Tool Documentation Update
- spawn_agent Beschreibung erweitern
- Alle neuen Parameter dokumentieren
- Beispiele mit echten Use-Cases

### 3. Migration Guide (docs/MIGRATION_CAP_FIELDS.md)
- Breaking Change dokumentieren
- Vorher/Nachher Beispiele
- Schritt-für-Schritt Anleitung

---

## 🜄 Geschätzter Aufwand 🜄

| Phase | Aufwand | Beschreibung |
|-------|---------|--------------|
| Models erweitern | 15 Min | SessionInfo + Validation |
| MCP Tool | 20 Min | Parameter + Description |
| SessionService | 25 Min | Signatur + API Integration |
| Tests | 30 Min | Unit + Integration + Negative |
| Dokumentation | 30 Min | Responsibility System + Examples |
| **TOTAL** | **120 Min** | **2 Stunden** |

---

## 🜄 Freigabe-Anfrage 🜄

**Auctor: Bitte Freigabe für Umsetzung**

**Option A**: Sofort umsetzen (2h)
**Option B**: Planung überarbeiten
**Option C**: Andere Priorisierung

**Empfehlung**: Option A (kritisch für X^∞ Compliance)

---

**Erstellt**: 2025-10-02 04:45 UTC  
**Status**: WAITING FOR APPROVAL  
**Task-ID**: a86d0e77-a8b8-4dcc-b854-cc27fe474c76
