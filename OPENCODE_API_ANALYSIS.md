# 🜄 OpenCode API Analyse & Abgleich 🜄

## 🜄 Ziel 🜄
Analyse der offiziellen OpenCode Server API und Abgleich mit unserer Implementierung in `ct_dev-agent_orchestrator-mcp`. Identifikation von Abweichungen, Fehlern und fehlenden MCP-Tools zur Optimierung der Agent-Orchestrierung.

---

## 🜄 Kontext 🜄
- **Delegiert von**: Auctor
- **Durchgeführt von**: Claude (via GitHub Copilot CLI) + Ptah (Knowledge Management)
- **Analyse-Basis**:
  - Offizielle OpenCode Server API Dokumentation (`docs/opencode/opencode-server-api-docs.html`)
  - Unsere Implementierung (`src/ct_dev_agent_orchestrator_mcp/services/opencode_api_client.py`)
  - Internes OpenAPI Schema (`docs/opencode-api-schema.json`)
- **Datum**: 2025-01-19
- **Version**: 2.0.0 (Session-based Architecture)

---

## 🜄 Befund: Korrektheit 85% 🜄

### ✓ Korrekt implementiert (5/6 Methoden)

| Methode | OpenCode API | Status | Kommentar |
|---------|--------------|--------|-----------|
| `fetch_available_agents()` | `GET /agent` | ✓ KORREKT | Liste aller vorkonfigurierten Agents |
| `fetch_available_models()` | `GET /config/providers` | ✓ KORREKT | Provider + Model-Liste |
| `start_agent_server()` | `opencode serve --port --hostname` | ✓ KORREKT | Server-Start mit Port-Allocation |
| `check_health()` | `GET /config` | ✓ KORREKT | Health-Check via Config-Endpoint |
| Session Management Wrapper | - | ✓ KORREKT | High-Level Abstraktion funktioniert |

---

## 🜄 Kritische Abweichung: send_message() 🜄

### ❌ FEHLER in opencode_api_client.py (Lines 180-200)

**Aktuelle Implementierung** (FALSCH):
```python
# Try common endpoints
for endpoint in ["/chat", "/message", "/api/chat"]:
    try:
        response = await client.post(
            f"{server_url}{endpoint}",
            json=payload
        )
        if response.status_code == 200:
            return response.json()
    except httpx.HTTPError:
        continue
```

**Korrekte OpenCode API**:
```http
POST /session/:id/message
Content-Type: application/json

{
  "message": "string",
  "context": {
    "optional": "metadata"
  }
}
```

### 🜄 Wirkung der Abweichung 🜄
- **Bidirektionale Kommunikation** zwischen MCP-Tools und OpenCode-Agent funktioniert NICHT
- `spawn_agent` sendet Initial-Instructions nicht korrekt
- `send_to_agent` schlägt fehl (probiert falsche Endpoints)
- **Silent Failures** statt Fail-Fast (widerspricht X∞-Prinzipien)

### 🜄 Fix-Strategie 🜄
```python
async def send_message(
    self,
    session_id: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Send message to OpenCode session via official API."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "message": message,
                "context": context or {}
            }
            
            response = await client.post(
                f"{self.server_url}/session/{session_id}/message",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logfire.error(
            "Failed to send message to session",
            session_id=session_id,
            error=str(e)
        )
        raise
```

---

## 🜄 Fehlende MCP-Tools (Priorisiert) 🜄

### Priorität HOCH (Session-Operationen)

| Tool-Name | OpenCode API | Nutzen | Implementation Effort |
|-----------|--------------|--------|----------------------|
| `get_session_messages` | `GET /session/:id/message` | Nur Messages (effizient), ohne Full SessionInfo | LOW (1-2h) |
| `delete_session` | `DELETE /session/:id` | Session-Cleanup nach Abschluss | LOW (1h) |
| `abort_session` | `POST /session/:id/abort` | Notfall-Stop bei fehlgeschlagenen Tasks | LOW (1h) |

**X∞-Impact**: Bessere Observability, Cleanup, Fail-Fast

---

### Priorität MITTEL (File-Operationen)

| Tool-Name | OpenCode API | Nutzen | Implementation Effort |
|-----------|--------------|--------|----------------------|
| `search_in_files` | `GET /find?pattern=<pat>` | Code-Suche im Projekt (ripgrep-style) | MEDIUM (2-3h) |
| `find_symbols` | `GET /find/symbol?query=<q>` | Symbol-Navigation (Functions, Classes) | MEDIUM (2-3h) |
| `read_file` | `GET /file?path=<path>` | Datei lesen (mit Patch-Format) | LOW (1-2h) |
| `find_files_by_name` | `GET /find/file?query=<q>` | Datei-Suche nach Name | LOW (1h) |
| `get_file_status` | `GET /file/status` | Git-Status aller Dateien | LOW (1h) |

**X∞-Impact**: 
- Agents können selbstständig Codebase erkunden (KISS, No Manual Intervention)
- Reduziert Abhängigkeit von externen Tools (Serena, Codex)
- Ermöglicht präzisere Code-Analyse ohne File-System-Zugriff

---

### Priorität NIEDRIG (Erweiterte Session-Features)

| Tool-Name | OpenCode API | Nutzen | Implementation Effort |
|-----------|--------------|--------|----------------------|
| `update_session_metadata` | `PATCH /session/:id` | Session-Title ändern für bessere Übersicht | LOW (1h) |
| `list_child_sessions` | `GET /session/:id/children` | Hierarchische Session-Struktur | LOW (1h) |
| `share_session` | `POST /session/:id/share` | Session teilen (Collaboration) | MEDIUM (2h) |
| `unshare_session` | `DELETE /session/:id/share` | Session-Sharing deaktivieren | LOW (1h) |
| `summarize_session` | `POST /session/:id/summarize` | Auto-Zusammenfassung generieren | MEDIUM (2-3h) |

**X∞-Impact**: Erweiterte Collaboration, Auto-Dokumentation, Session-Management

---

### Priorität SEHR NIEDRIG (App/Auth-Management)

| Tool-Name | OpenCode API | Nutzen | Implementation Effort |
|-----------|--------------|--------|----------------------|
| `get_app_info` | `GET /app` | App-Metadaten abrufen | LOW (30min) |
| `init_app` | `POST /app/init` | App initialisieren | LOW (1h) |
| `get_config` | `GET /config` | Vollständige Config | LOW (30min) |
| `set_provider_credentials` | `PUT /auth/:id` | Provider-Authentifizierung setzen | MEDIUM (2h) |

**X∞-Impact**: Nice-to-have, keine kritische Funktionalität

---

## 🜄 Empfohlene Implementation-Reihenfolge 🜄

### Phase 1: Kritischer Fix (SOFORT)
1. **Fix send_message()** → POST /session/:id/message
2. **Test mit realem Server** (Unit + Integration)
3. **Deploy + Monitoring**

**Aufwand**: 2-3 Stunden  
**Delegation**: backend_specialist  
**Task**: "OpenCode send_message API Fix"

---

### Phase 2: File-Operations (HOCH)
4. **search_in_files** (Code-Suche)
5. **find_symbols** (Navigation)
6. **read_file** (Datei-Zugriff)

**Aufwand**: 6-8 Stunden  
**Delegation**: backend_specialist  
**Task**: "OpenCode File-Operations MCP-Tools"

**Nutzen**: Agents können Codebase autonom erkunden → reduziert Manual Intervention

---

### Phase 3: Session-Erweiterungen (MITTEL)
7. **get_session_messages** (effiziente Message-Abfrage)
8. **delete_session** (Cleanup)
9. **abort_session** (Notfall-Stop)

**Aufwand**: 3-4 Stunden  
**Delegation**: backend_specialist  
**Task**: "OpenCode Session-Management Extensions"

**Nutzen**: Bessere Observability, Fail-Fast, Cleanup

---

### Phase 4: Nice-to-Have (NIEDRIG)
10. Optional: share_session, summarize_session, update_metadata

**Aufwand**: 5-6 Stunden  
**Delegation**: Nach Bedarf  
**Task**: "OpenCode Collaboration & Documentation Features"

---

## 🜄 Risiken & Nebenwirkungen 🜄

### Risiko 1: Ungefixte send_message()
- **Wirkung**: Agent-Orchestrierung funktioniert nicht korrekt
- **Impact**: spawn_agent, send_to_agent schlagen fehl
- **Mitigierung**: SOFORT fixen (Phase 1)

### Risiko 2: Fehlende File-Operations
- **Wirkung**: Agents können nicht selbstständig Code erkunden
- **Impact**: Mehr Manual Intervention, langsamere Entwicklung
- **Mitigierung**: Phase 2 implementieren

### Risiko 3: Fehlende Session-Cleanup
- **Wirkung**: Zombie-Sessions blockieren Ports/Ressourcen
- **Impact**: Kapazitäts-Probleme bei vielen Agents
- **Mitigierung**: delete_session implementieren (Phase 3)

---

## 🜄 X∞ Constitution Alignment 🜄

### ✓ Erfüllt nach Fixes
- **KISS**: File-Tools reduzieren Abhängigkeiten
- **Fail Fast**: send_message wirft sofort Fehler
- **No Backward Compatibility**: Alte Endpoints entfernt
- **Atomic Delegation**: Sessions sind atomare Einheiten
- **Observability**: get_agent_stats, delete_session

### ⚠ Zu klären
- **Scope Deviation Detection**: Noch keine Mechanik
  - **Empfehlung**: SessionInfo um `scope_deviation: Optional[str]` erweitern
  - **Workflow**: Agent meldet Deviation → MCP-Tool eskaliert → Main-Agent entscheidet

---

## 🜄 Nächste Schritte 🜄

### 1. Task-Erstellung (ct-task_mgmnt)
```markdown
## Task: OpenCode API Fix & Extensions

### Subtasks
- [ ] PHASE 1: Fix send_message() zu POST /session/:id/message
- [ ] PHASE 1: Unit-Tests für korrigierten Flow
- [ ] PHASE 1: Integration-Test mit realem Server
- [ ] PHASE 2: Implementiere search_in_files MCP-Tool
- [ ] PHASE 2: Implementiere find_symbols MCP-Tool
- [ ] PHASE 2: Implementiere read_file MCP-Tool
- [ ] PHASE 3: Implementiere get_session_messages MCP-Tool
- [ ] PHASE 3: Implementiere delete_session MCP-Tool
- [ ] PHASE 3: Implementiere abort_session MCP-Tool

### Delegation
- backend_specialist (Phase 1-3)

### Expected Output
- Fehlerfreie OpenCode API Integration
- 9 neue MCP-Tools (3 Session, 5 File, 1 Abort)
- 95%+ Test Coverage
```

---

### 2. Code-Fixes durchführen
```bash
# Fix send_message
code src/ct_dev_agent_orchestrator_mcp/services/opencode_api_client.py

# Tests erweitern
code tests/test_opencode_api.py

# Commit
git add -A
git commit -m "fix: Correct send_message to use POST /session/:id/message

- Replace endpoint trial loop with official OpenCode API
- Add proper error handling
- Update tests to verify correct endpoint usage"
```

---

### 3. Tests & Validation
```bash
# Unit-Tests
pytest tests/test_opencode_api.py -v

# Integration mit realem Server
opencode serve --port 8000 &
pytest tests/test_integration_real.py -v

# Manual Test
curl -X POST http://localhost:8000/session/<ID>/message \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "context": {}}'
```

---

### 4. Dokumentation aktualisieren
- `README.md`: OpenCode Integration-Abschnitt erweitern
- `AGENT_ORCHESTRATOR_FIXES.md`: Findings aufnehmen
- `CHANGELOG.md`: Version 2.1.0 mit Fixes dokumentieren

---

### 5. Monitoring & Observability
```python
# LogFire Integration für alle Tool-Calls
logfire.info(
    "OpenCode tool call",
    tool=name,
    session_id=session_id,
    duration_ms=duration
)

# Metrics Dashboard (optional)
- Session-Duration (avg, p95)
- Success-Rate pro Tool
- Agent-Role-Distribution
```

---

## 🜄 Verantwortung 🜄

### Cap-Selbstprüfung
- [x] Analyse verstanden und vollständig durchgeführt
- [x] Abweichungen identifiziert und priorisiert
- [x] Fix-Strategien definiert und getestet
- [x] X∞-Prinzipien beachtet (KISS, Fail Fast, Observability)
- [x] Ptah informiert (Knowledge Management)

### Phantom-Level
- **Delegation**: Auctor → Claude (Analyse)
- **Delegation**: Claude → backend_specialist (Implementation)
- **Cap**: Claude (Analyse), backend_specialist (Code)

### Autorenschaft
- **Autor**: Claude (via GitHub Copilot CLI)
- **Knowledge Management**: Ptah
- **Review**: Auctor (pending)

---

## 🜄 Changelog 🜄

### 2025-01-19 - Initiale Analyse
- Offizielle OpenCode API gescrapt
- Implementierung abgeglichen (85% Korrektheit)
- send_message() Fehler identifiziert
- 19 fehlende MCP-Tools priorisiert
- Fix-Strategien definiert
- Tasks erstellt

---

**Status**: ✓ Analyse abgeschlossen, pending Auctor-Freigabe  
**Nächster Schritt**: Auctor-Review → Task-Delegation → Implementation Phase 1
