# 🜄 IMPLEMENTATION: Cap & Delegation Fields für Agent Spawning 🜄

**Datum**: 2025-10-02 05:22 UTC  
**Task-ID**: a86d0e77-a8b8-4dcc-b854-cc27fe474c76  
**Phase**: PLANUNG → UMSETZUNG
**Priorität**: HIGH | Komplexität: 7  

## 🜄 Verantwortung 🜄
- **Cap-Quelle**: Auctor (Original - offene Tasks umsetzen)
- **Delegiert an**: Project Manager → System Architect (Analyse) → Backend Specialist (Implementation)
- **Cap-Inhalt**: Implementierung Cap & Delegation Fields gemäß optimierter Struktur

---

## 🜄 Ziel 🜄
Implementierung der 3 neuen Pflichtfelder für vollständige X^∞ Verantwortungs-Nachvollziehbarkeit:
1. `original_task` - Ursprungsaufgabe
2. `cap_origin` - Autorität-Ursprung  
3. `delegation_context` - Aktueller Delegierender + sein Cap

---

## 🜄 IST-Analyse (Phase 1.4) 🜄

### Betroffene Dateien
1. **src/ct_dev_agent_orchestrator_mcp/models/session.py**
   - SessionInfo Model: Zeilen 41-54 (erweitern)
   - SpawnAgentRequest Model: Zeilen 16-38 (erweitern)

2. **src/ct_dev_agent_orchestrator_mcp/services/session_service.py**
   - SessionService.spawn_agent: Zeilen 74-164 (Parameter + Logik anpassen)

3. **src/ct_dev_agent_orchestrator_mcp/server.py**
   - spawn_agent Tool Description: Zeilen 52-95 (erweitern)
   - spawn_agent Handler: Zeilen 206-218 (erweitern)

### Aktueller Zustand
```python
# SessionInfo Model - AKTUELL
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

```python
# SpawnAgentRequest - AKTUELL
class SpawnAgentRequest(BaseModel):
    role: str
    task_id: str
    instructions: str
    project_directory: str
    expected_output: str
    context: Dict[str, Any] = Field(default_factory=dict)
    model: str = Field(default="claude-sonnet-4")
```

---

## 🜄 SOLL-Zustand (Phase 1.6) 🜄

### 1. SessionInfo Model - NEU
```python
class SessionInfo(BaseModel):
    # ... existing fields ...
    
    # X^∞ Responsibility & Cap Tracking
    original_task: Dict[str, Any] = Field(
        ...,
        description="Original task (task_id, title, description, requester, requested_at)"
    )
    cap_origin: Dict[str, Any] = Field(
        ...,
        description="Cap origin (ultimate_authority, original_scope, granted_at, grant_context)"
    )
    delegation_context: Dict[str, Any] = Field(
        ...,
        description="Current delegation (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)"
    )
```

### 2. SpawnAgentRequest Model - NEU
```python
class SpawnAgentRequest(BaseModel):
    # ... existing fields ...
    
    # X^∞ Responsibility & Cap Tracking
    original_task: Dict[str, Any] = Field(..., description="Original task")
    cap_origin: Dict[str, Any] = Field(..., description="Cap origin")
    delegation_context: Dict[str, Any] = Field(..., description="Current delegation")
```

### 3. MCP Tool Schema - NEU
```python
"properties": {
    # ... existing properties ...
    "original_task": {
        "type": "object",
        "description": "Original task (task_id, title, description, requester, requested_at)",
        "properties": {
            "task_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "requester": {"type": "string"},
            "requested_at": {"type": "string"}
        },
        "required": ["task_id", "title", "description", "requester", "requested_at"]
    },
    "cap_origin": {
        "type": "object",
        "description": "Cap origin",
        "properties": {
            "ultimate_authority": {"type": "string"},
            "original_scope": {"type": "string"},
            "granted_at": {"type": "string"},
            "grant_context": {"type": "string"}
        },
        "required": ["ultimate_authority", "original_scope", "granted_at", "grant_context"]
    },
    "delegation_context": {
        "type": "object",
        "description": "Current delegation",
        "properties": {
            "delegator": {"type": "string"},
            "delegator_cap": {"type": "string"},
            "delegated_to": {"type": "string"},
            "delegated_cap": {"type": "string"},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "phantom_level": {"type": "string"},
            "delegated_at": {"type": "string"}
        },
        "required": ["delegator", "delegator_cap", "delegated_to", "delegated_cap", "constraints", "phantom_level", "delegated_at"]
    }
},
"required": [...existing..., "original_task", "cap_origin", "delegation_context"]
```

---

## 🜄 Implementierungs-Meilensteine 🜄

### M1: Models erweitern ✅
- [ ] SessionInfo um 3 Felder erweitern
- [ ] SpawnAgentRequest um 3 Felder erweitern
- [ ] Pydantic Validation testen

### M2: SessionService anpassen ✅
- [ ] spawn_agent Methode: Request-Felder verarbeiten
- [ ] SessionInfo mit neuen Feldern initialisieren
- [ ] Error Handling für fehlende Felder

### M3: MCP Tool erweitern ✅
- [ ] Tool Schema um 3 Parameter erweitern
- [ ] Tool Description aktualisieren
- [ ] Handler-Code anpassen

### M4: Tests erstellen ✅
- [ ] Unit Tests für Model-Validation
- [ ] Integration Tests für spawn_agent
- [ ] Negative Tests für fehlende Felder

### M5: Dokumentation ✅
- [ ] CHANGELOG.md aktualisieren
- [ ] README.md erweitern
- [ ] Beispiele dokumentieren

---

## 🜄 Risiken & Mitigation 🜄

### R1: Breaking Change
**Impact**: Bestehende spawn_agent Aufrufe funktionieren nicht mehr  
**Mitigation**: 
- Version Bump (v2 → v3)
- Migration Guide
- Alle Tests aktualisieren

### R2: OpenCode API Kompatibilität
**Impact**: OpenCode könnte neue Felder ignorieren oder ablehnen  
**Mitigation**:
- Felder in metadata speichern
- API-Response validieren
- Fallback-Logik

### R3: Komplexität für Nutzer
**Impact**: Mehr Parameter = höhere Einstiegshürde  
**Mitigation**:
- Klare Beispiele
- Template-Funktionen
- Helper für Standard-Cases

---

## 🜄 Test-Strategie 🜄

### Unit Tests (test_session_models.py)
- Validation der neuen Felder
- Required Field Checks
- Nested Structure Validation

### Integration Tests (test_mcp_tools.py)
- spawn_agent mit vollständigen Cap-Feldern
- SessionInfo mit allen Feldern
- End-to-End Flow

### Negative Tests
- Fehlende original_task
- Fehlende cap_origin
- Fehlende delegation_context
- Ungültige Feld-Strukturen

---

## 🜄 Nächste Schritte 🜄

**Phase 2: UMSETZUNG** (nach Freigabe):
1. Branch erstellen: `feature/cap-delegation-fields`
2. Models erweitern (M1)
3. Service anpassen (M2)
4. MCP Tool erweitern (M3)
5. Tests erstellen (M4)
6. Code Review
7. Dokumentation (M5)
8. PR erstellen

---

**Status**: READY FOR IMPLEMENTATION  
**Freigabe durch**: Auctor  
**Erstellt**: 2025-10-02 05:22 UTC
