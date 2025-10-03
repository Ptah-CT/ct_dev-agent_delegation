# API-Endpunkt zu MCP-Tool Mapping Analyse

## 🜄 Ziel 🜄
Systematische Validierung aller OpenCode API-Endpunkte gegen MCP-Tool-Expositionen zur Identifikation von Redundanzen und fehlenden Mappings.

## 🜄 Kontext 🜄
- Projekt: ct_dev-agent_orchestrator
- Branch: feature/opencode-api-integration
- Datum: 2025-10-03
- Task: 42419ca4-c347-4afc-9b08-33cb085ef420

## 🜄 Verantwortung 🜄
- Autor: Claude (Code Analysis Agent)
- Delegiert von: Auctor
- Cap: Technische Analyse und Dokumentation

---

## 1. Exponierte MCP-Tools (server.py)

### Session-based Tools (V2)
1. **spawn_agent** - Spawnt Agent-Session mit X^∞ Responsibility Tracking
2. **query_session** - Status einer Agent-Session abfragen
3. **get_agent_output** - Finales Output einer abgeschlossenen Session
4. **list_active_sessions** - Alle aktiven Sessions auflisten
5. **stop_agent** - Agent-Session stoppen
6. **send_to_agent** - Follow-up Message an laufende Session

### OpenCode Discovery Tools
7. **list_opencode_agents** - Alle verfügbaren Agents vom OpenCode Server
8. **list_opencode_models** - Alle verfügbaren Models mit Provider-Info
9. **get_agent_capabilities** - Agent-Capabilities vom OpenCode Server

### Agent Management Tools  
10. **list_agents** - Alle aktiven Agent-Instanzen
11. **get_agent_stats** - Agent-Statistiken (Count by Status)

**Gesamt: 11 Tools**

---

## 2. KRITISCHE REDUNDANZEN

### 2.1 Doppelte Tool-Definition
**get_agent_capabilities** ist ZWEIMAL in der Tool-Liste definiert (Zeile ~217 und ~231 in server.py)

**Wirkung:**
- Potenzielle Konflikte bei Tool-Auflösung
- Verwirrung für Clients
- Redundanter Code

**Empfehlung:**
- [ ] Eine Definition entfernen
- [ ] Prüfen welche Implementierung korrekt ist
- [ ] Code Review durchführen

---

## 3. API-Client Methoden Mapping

### 3.1 OpenCodeAPIClient (opencode_api_client.py)

| Methode | Als Tool exponiert | Verwendung | Status |
|---------|-------------------|------------|--------|
| `fetch_available_agents` | ✓ (list_opencode_agents) | Direkt in Tool-Handler | OK |
| `fetch_available_models` | ✓ (list_opencode_models via list_providers) | Indirekt über list_providers | OK |
| `start_agent_server` | ✓ | Intern in SessionService.spawn_agent | OK |
| `stop_agent_server` | ✓ | Intern in stop_agent | OK |
| `check_health` | ✓ | Intern in _wait_for_health | OK |
| `send_message` | ✓ | Intern in send_to_agent | OK |
| `get_process_info` | ✗ | Intern verfügbar | FEHLENDES TOOL |
| `cleanup` | ✗ | Intern in shutdown | OK (kein Tool nötig) |
| `_get_next_port` | N/A | Private Methode | OK |
| `_fetch_models_from_cli` | N/A | Private Methode | OK |

### 3.2 OpenCodeService (opencode_service.py)

| Methode | Als Tool exponiert | Verwendung | Status |
|---------|-------------------|------------|--------|
| `start_agent` | ✓ | Intern in SessionService | OK |
| `stop_agent` | ✓ | Intern in stop_agent Tool | OK |
| `check_health` | ✓ | Intern in query_session | OK |
| `get_agent_metrics` | ✗ | Nicht verwendet | FEHLENDES TOOL |
| `get_agent_output` | ✓ | In get_agent_output Tool | OK |
| `restart_agent` | ✗ | Nicht verwendet | FEHLENDES TOOL |
| `get_all_process_states` | ✗ | Nicht verwendet | FEHLENDES TOOL |
| `send_request` | ✓ | Intern in send_to_agent | OK |

---

## 4. Fehlende Tool-Expositionen

### 4.1 Nützliche aber nicht exponierte Methoden

#### get_process_info (OpenCodeAPIClient)
**Zweck:** Informationen über laufenden Agent-Prozess
**Potentieller Nutzen:** Debugging, Monitoring
**Empfehlung:** 
- [ ] Als Tool `get_process_info` exponieren
- [ ] Oder: In `query_session` integrieren

#### get_agent_metrics (OpenCodeService)
**Zweck:** Agent-Metriken abrufen
**Potentieller Nutzen:** Performance-Monitoring, Debugging
**Empfehlung:**
- [ ] Als Tool `get_agent_metrics` exponieren
- [ ] Oder: In `get_agent_stats` integrieren

#### restart_agent (OpenCodeService)
**Zweck:** Agent neu starten
**Potentieller Nutzen:** Recovery bei Fehlern
**Empfehlung:**
- [ ] Als Tool `restart_agent` exponieren
- [ ] Wichtig für robuste Session-Verwaltung

#### get_all_process_states (OpenCodeService)
**Zweck:** Status aller Prozesse
**Potentieller Nutzen:** System-Übersicht, Debugging
**Empfehlung:**
- [ ] Prüfen ob redundant mit `get_agent_stats`
- [ ] Eventuell in `get_agent_stats` integrieren

---

## 5. Redundanzen mit anderen MCP-Servern

### 5.1 Potenzielle Überschneidung mit ct-task_orchestrator
Laut Ptah-Kontext gibt es Überschneidungen:
- Task-Creation (beide handhaben Tasks)
- Project-Strukturen (ähnlich zu GitHub Issues)

**ABER:** Im aktuellen Code KEINE direkte Redundanz sichtbar
- ct_dev-agent_orchestrator fokussiert auf Agent-Orchestrierung
- Keine Task-CRUD-Operationen im Agent-Orchestrator

**Empfehlung:**
- [ ] Keine Aktion nötig
- [ ] Klare Verantwortungstrennung ist vorhanden

---

## 6. Code-Qualität Issues

### 6.1 Doppelte get_agent_capabilities Definition
```python
# Zeile ~217
Tool(
    name="get_agent_capabilities",
    description="Gets information about available agent roles and capabilities",
    ...
)

# Zeile ~231 (REDUNDANT!)
Tool(
    name="get_agent_capabilities",
    description="Gets information about available agent roles and capabilities from OpenCode Server. Returns list of agents with their names, descriptions, and configurations.",
    ...
)
```

**Kritikalität:** HIGH
**Fix:** Eine Definition entfernen

### 6.2 Inkonsistente Beschreibungen
`list_opencode_agents` und `get_agent_capabilities` scheinen ähnliche Funktionalität zu bieten.

**Empfehlung:**
- [ ] Funktionale Unterschiede klären
- [ ] Eine konsolidieren oder klar abgrenzen

---

## 7. Zusammenfassung

### 🜄 Kritische Findings 🜄
1. **REDUNDANZ:** `get_agent_capabilities` zweimal definiert
2. **FEHLENDES TOOL:** `get_process_info` könnte nützlich sein
3. **FEHLENDES TOOL:** `restart_agent` fehlt für robuste Recovery
4. **FEHLENDE TOOLS:** `get_agent_metrics`, `get_all_process_states` nicht exponiert

### 🜄 Empfehlungen 🜄
**Priorität HIGH:**
- [ ] Doppelte `get_agent_capabilities` Definition entfernen
- [ ] `restart_agent` als Tool exponieren

**Priorität MEDIUM:**
- [ ] `get_process_info` exponieren oder in `query_session` integrieren
- [ ] `get_agent_metrics` exponieren oder in `get_agent_stats` integrieren
- [ ] Funktionale Abgrenzung zwischen `list_opencode_agents` und `get_agent_capabilities` klären

**Priorität LOW:**
- [ ] `get_all_process_states` prüfen (eventuell redundant)

### 🜄 Risiken 🜄
- Doppelte Tool-Definition kann zu Runtime-Fehlern führen
- Fehlende `restart_agent` Funktion reduziert Robustheit
- Inkonsistenzen könnten Entwickler verwirren

---

## 🜄 Nächste Schritte 🜄
- [ ] Issue für Redundanz-Fix erstellen
- [ ] Code Review für fehlende Tools durchführen
- [ ] Ptah über Findings informieren
- [ ] Update in Task ct_dev-task_orchestrator dokumentieren
