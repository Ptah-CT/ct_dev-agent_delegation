# 🜄 Planung: Behebung asyncio-Fehler im spawn_agent Tool 🜄

## 🜄 Ziel 🜄
Behebung des Fehlers "cannot access local variable 'asyncio' where it is not associated with a value" im spawn_agent MCP Tool.

## 🜄 Kontext 🜄
- **Fehler**: asyncio-Scope-Problem beim Tool-Aufruf
- **Betroffenes Tool**: agent_orchestrator MCP - spawn_agent
- **Funktionale Tools**: get_agent_capabilities, list_agents, get_agent_stats, list_active_sessions
- **Status**: Analyse-Phase (PLAN mode - keine Code-Änderungen)

## 🜄 Verantwortung 🜄
- **Autor**: Claude (Project Manager Role)
- **Delegation**: Von Auctor für Fehlerbehebung
- **Cap**: Testing & Fixing authority
- **Phantom-Level**: Delegation/Cap

## 🜄 Ist-Zustand 🜄

**Betroffene Datei**: `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`

**Code-Struktur**:
- Zeile 12: `import asyncio` (top-level import)
- Zeile 149: `import asyncio` (redundanter lokaler Import in spawn_agent Methode)
- Zeile 157: `except asyncio.TimeoutError as e:` (Verwendung von asyncio)

**Problem**: Redundanter lokaler Import von asyncio innerhalb der spawn_agent Methode.

## 🜄 Root Cause 🜄

**Fehler**: "cannot access local variable 'asyncio' where it is not associated with a value"

**Ursache**: Python Scoping-Problem bei lokalen Imports:

1. asyncio wird auf Zeile 12 als top-level importiert
2. asyncio wird auf Zeile 149 ERNEUT lokal in spawn_agent() importiert
3. Python markiert asyncio als lokale Variable für die Funktion
4. Zeile 157 (except asyncio.TimeoutError) verwendet asyncio NACH dem lokalen Import
5. Python kompiliert die Funktion und erkennt: lokale Variable asyncio wird verwendet, bevor sie definiert ist

**Mechanismus**:
- Lokale Imports überschreiben den globalen Scope innerhalb der Funktion
- Alle Verwendungen von asyncio in der Funktion beziehen sich auf die lokale Variable
- Die except-Klausel kommt nach dem Import, aber Python erkennt den Konflikt beim Kompilieren
- Resultat: "cannot access local variable where it is not associated with a value"

## 🜄 Zielzustand 🜄

**Lösung**: Entfernung des redundanten lokalen asyncio-Imports.

**Änderung**:
- Datei: `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`
- Zeile 149: `import asyncio` → **LÖSCHEN**

**Begründung**:
- Top-level Import auf Zeile 12 ist ausreichend
- Kein Bedarf für lokalen Re-Import
- Beseitigt Scoping-Konflikt

**Erwartetes Ergebnis**:
- spawn_agent Tool funktioniert ohne asyncio-Fehler
- Alle anderen MCP Tools bleiben unberührt
- Keine Seiteneffekte

## 🜄 Implementierungsplan 🜄

### Phase 1: Code-Änderung
- [ ] Zeile 149 in session_service.py löschen: `import asyncio`

### Phase 2: Validierung
- [ ] spawn_agent Tool testen
- [ ] Andere MCP Tools validieren (get_agent_capabilities, list_agents, etc.)
- [ ] Sicherstellen: keine Regressionen

### Phase 3: Dokumentation & Abschluss
- [ ] CHANGELOG.md aktualisieren
- [ ] Git commit mit aussagekräftiger Message
- [ ] Branch push
- [ ] Ptah über Abschluss informieren

## 🜄 Risiken 🜄
- Agent-Spawning-Funktionalität kritisch für Workflow
- Änderungen könnten andere MCP Tools beeinflussen
- Async-Änderungen können Deadlocks verursachen

## 🜄 Prüfung 🜄
- [ ] Code analysiert
- [ ] Root Cause identifiziert
- [ ] Fix-Strategie definiert
- [ ] Freigabe durch Auctor
- [ ] Implementation getestet
- [ ] Keine Seiteneffekte
