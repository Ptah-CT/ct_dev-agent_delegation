# Naming & Konzeptionelle Verbesserungen

## 🜄 Ziel 🜄
Verbesserung der API-Klarheit und Alignment mit X^∞ Philosophie durch präzisere Benennung und konzeptionelle Umstellung von "Sessions" auf "Delegations".

## 🜄 Kontext 🜄
- Projekt: ct_dev-agent_orchestrator
- Branch: feature/opencode-api-integration
- Feedback: Auctor
- Datum: 2025-10-03

## 🜄 Verantwortung 🜄
- Konzept: Auctor
- Dokumentation: Claude
- Cap: Systemische Konsistenz mit X^∞ Prinzipien

---

## 1. KRITISCHE NAMING-VERWIRRUNG

### 1.1 list_agents vs list_opencode_agents

**Aktueller Zustand:**
```python
# Tool 1: list_agents
# Funktion: Listet LAUFENDE Agent-Instanzen (konkrete Prozesse)
# Output: agent_id, role, status, port, PID

# Tool 2: list_opencode_agents  
# Funktion: Listet VERFÜGBARE Agent-Rollen (Templates vom Server)
# Output: name, description, mode, tools, model, temperature
```

**Problem:**
- Namen suggerieren identische Funktionalität
- Tatsächlich: Komplett unterschiedliche Konzepte
- User-Verwirrung garantiert

**Wirkung:**
- Entwickler rufen falsches Tool auf
- API ist nicht selbsterklärend
- Dokumentations-Overhead

### 1.2 Empfohlene Umbenennung

| Aktuell | Neu | Begründung |
|---------|-----|------------|
| `list_opencode_agents` | `list_available_agent_roles` | Klar: "verfügbare Rollen" |
| `list_agents` | `list_running_delegations` | Klar: "laufende Delegationen" |

**Alternative für list_agents:**
- `list_active_agents` (weniger radikal)
- `list_agent_instances` (technisch präzise)
- `list_running_delegations` (philosophisch korrekt)

---

## 2. SESSION → DELEGATION REFACTORING

### 2.1 Konzeptionelle Begründung

**X^∞ Philosophie:**
- Jede Agent-Aktivierung ist eine **Delegation von Verantwortung/Cap**
- "Session" ist neutraler Tech-Begriff ohne systemische Bedeutung
- "Delegation" macht Verantwortungskette explizit

**Aktuelles Problem:**
```python
session_service.spawn_agent(...)
# Impliziert: "Starte Session"
# Tatsächlich: "Delegiere Arbeit mit Cap-Transfer"
```

**Gewünschter Zustand:**
```python
delegation_service.spawn_delegation(...)
# Explizit: "Erstelle Delegation mit Cap-Kontext"
```

### 2.2 Vollständiges Refactoring-Mapping

#### Services
| Aktuell | Neu | Impact |
|---------|-----|--------|
| `SessionService` | `DelegationService` | Class rename |
| `session_service.py` | `delegation_service.py` | File rename |
| `session_manager.py` | BEHALTEN (technisch korrekt) | - |

#### Models
| Aktuell | Neu | Impact |
|---------|-----|--------|
| `Session` | `Delegation` | Model rename |
| `session.py` | `delegation.py` | File rename |
| `SpawnAgentRequest` | `SpawnDelegationRequest` | Model rename |
| `session_id` | `delegation_id` | Field rename |

#### MCP Tools
| Aktuell | Neu | Breaking Change |
|---------|-----|-----------------|
| `spawn_agent` | `delegate_task` oder `spawn_delegation` | YES |
| `query_session` | `query_delegation` | YES |
| `get_agent_output` | `get_delegation_output` | YES |
| `list_active_sessions` | `list_active_delegations` | YES |
| `stop_agent` | `stop_delegation` | YES |
| `send_to_agent` | `send_to_delegation` | YES |

#### Database
| Aktuell | Neu | Migration Required |
|---------|-----|-------------------|
| `sessions` table | `delegations` | YES |
| `session_id` column | `delegation_id` | YES |

---

## 3. ADDITIONAL REDUNDANZEN (aus vorheriger Analyse)

### 3.1 get_agent_capabilities (DOPPELT)
**Zeilen 217 und 231 in server.py**

**Action:**
- [ ] Zweite Definition entfernen
- [ ] Eventuell umbenennen zu `get_opencode_capabilities`

### 3.2 Konzeptionelle Überschneidung
`list_opencode_agents` und `get_agent_capabilities` liefern ähnliche Daten.

**Empfehlung:**
- [ ] `get_agent_capabilities` entfernen
- [ ] Funktionalität in `list_available_agent_roles` konsolidieren

---

## 4. VORGESCHLAGENES REFACTORING

### 4.1 Phase 1: Naming Fixes (Non-Breaking)

**Interne Umbenennung (kein API-Break):**
- [ ] `SessionService` → `DelegationService` (internal)
- [ ] `session.py` → `delegation.py` (internal)
- [ ] Model `Session` → `Delegation` (internal)

**API-Ergänzungen (Backwards Compatible):**
- [ ] Neue Tools mit korrekten Namen hinzufügen
- [ ] Alte Tools als @deprecated markieren
- [ ] Beide Versionen parallel für 1 Release

### 4.2 Phase 2: Agent Naming (Non-Breaking)

**Neue Tools:**
- [ ] `list_available_agent_roles` (ersetzt `list_opencode_agents`)
- [ ] `list_running_delegations` (ersetzt `list_agents`)

**Deprecation:**
- [ ] `list_opencode_agents` → Warnung + Redirect
- [ ] `list_agents` → Warnung + Redirect

### 4.3 Phase 3: Breaking Changes

**Nach Deprecation-Period:**
- [ ] Alte Tools entfernen
- [ ] Database Migration
- [ ] Changelog dokumentieren

---

## 5. IMPACT ANALYSE

### 5.1 Breaking Changes
**Betroffen:**
- Alle MCP-Clients die diese Tools nutzen
- Database Schema
- Interne Service-Calls

**Anzahl betroffener Stellen:**
- ~50 Files (geschätzt)
- ~200 Function Calls (geschätzt)

### 5.2 Migration Aufwand

| Komponente | Aufwand | Risiko |
|------------|---------|--------|
| Model Rename | 2h | LOW |
| Service Rename | 3h | LOW |
| Database Migration | 4h | MEDIUM |
| MCP Tool Updates | 2h | LOW |
| Testing | 8h | MEDIUM |
| **TOTAL** | **19h** | **MEDIUM** |

---

## 6. EMPFOHLENE VORGEHENSWEISE

### 6.1 Sofort (Minimal-Invasiv)

**Keine Breaking Changes:**
1. Doppelte `get_agent_capabilities` entfernen
2. Dokumentation verbessern:
   - Klar dokumentieren was `list_agents` vs `list_opencode_agents` tut
   - Beispiele in Docstrings

### 6.2 Kurzfristig (1-2 Sprints)

**Mit Deprecation-Strategie:**
1. Neue Tools mit korrekten Namen:
   - `list_available_agent_roles`
   - `list_running_delegations`
2. Alte Tools beibehalten mit Deprecation-Warnung
3. Interne Umbenennung (Session → Delegation)

### 6.3 Mittelfristig (3-4 Sprints)

**Breaking Changes:**
1. Alte Tools entfernen
2. Database Migration
3. Vollständige Umstellung

---

## 🜄 Risiken 🜄

**Breaking Changes:**
- Alle existierenden Clients brechen
- Downtime während Migration
- Dokumentations-Aufwand

**Philosophische Inkonsistenz:**
- "Session" verstößt gegen X^∞ Prinzipien
- Verantwortungskette nicht explizit
- Cap-System wird verschleiert

**Opportunitäts-Ethik:**
- Jede verzögerte Umbenennung erhöht Technical Debt
- Mehr Code wird auf falschem Konzept aufgebaut
- Spätere Migration wird teurer

---

## 🜄 Nächste Schritte 🜄

**Entscheidung erforderlich:**
- [ ] Freigabe für Phase 1 (Non-Breaking) durch Auctor
- [ ] Timeline für Breaking Changes festlegen
- [ ] Migration-Strategie mit Team besprechen

**Technische Vorbereitung:**
- [ ] Task im ct_dev-task_orchestrator erstellen
- [ ] Detailliertes Refactoring-Ticket mit Sub-Tasks
- [ ] Test-Strategie definieren

**Kommunikation:**
- [ ] Ptah informieren über konzeptionelle Änderung
- [ ] Breaking Changes dokumentieren
- [ ] Migration Guide für Clients erstellen
