# 🜄 Implementierungsplan: OpenCode Phase 1 Fix & Deviation Detection 🜄

## 🜄 Ziel 🜄
Abschluss der Phase 1 Fixes für OpenCode API-Integration durch:
1. Behebung Import-Fehler in session.py
2. Integration der Scope Deviation Detection
3. Erstellung vollständiger Tests mit >80% Coverage
4. Validierung der gesamten Implementierung

**Erwartetes Ergebnis**: Funktionsfähige bidirektionale Kommunikation mit OpenCode API, automatische Scope-Abweichungserkennung, vollständige Test-Coverage.

---

## 🜄 Kontext / Referenz 🜄

**Task-ID**: `6813741a-7f89-421e-86a0-672021f61ef2`  
**Status**: in-progress → wird auf completed gesetzt nach erfolgreicher Umsetzung  
**Priority**: HIGH  
**Complexity**: 8

**Vorarbeiten**:
- ✅ send_message() Endpoint Fix implementiert (POST /session/:id/message)
- ✅ SessionInfo Model um scope_deviation Feld erweitert
- ✅ ScopeDeviationDetector Klasse vollständig implementiert (utils/scope_deviation.py)
- ⏳ Import-Fehler in session.py (Optional nicht importiert)
- ⏳ Deviation Detection nicht integriert in Session-Lifecycle
- ⏳ Tests fehlen komplett

**Referenz-Dokumente**:
- OPENCODE_API_ANALYSIS.md
- V2_MIGRATION_TASKS.md
- docs/api-validation-report.md

---

## 🜄 Verantwortung / Authority 🜄

**Autor**: GitHub Copilot CLI (Project Manager Rolle)  
**Delegation**: Von Auctor  
**Cap**: Planung & Koordination  
**Phantom-Level**: Delegation/Cap [x]

**Umsetzung durch Experten**:
- Import-Fix: Syntax Reviewer
- Integration: Backend Specialist + System Integrator
- Tests: QA Specialist
- Reviews: Code Reviewer + Philosophical Reviewer

---

## 🜄 Implementierung - Detaillierte Schritte 🜄

### Phase 1.1: Import-Fehler beheben (KRITISCH)
**Verantwortlich**: Syntax Reviewer  
**Geschätzte Zeit**: 5 Minuten  
**Datei**: `src/ct_dev_agent_orchestrator_mcp/models/session.py`

**Aufgabe**:
- [ ] Import von `Optional` aus typing hinzufügen
- [ ] Zeile 2 ändern von:
  ```python
  from typing import Dict, Any, List
  ```
  zu:
  ```python
  from typing import Dict, Any, List, Optional
  ```
- [ ] Import testen: `python3 -c "from src.ct_dev_agent_orchestrator_mcp.models.session import SessionInfo"`
- [ ] Verify: Kein NameError mehr

**Erfolgs-Kriterium**: Import funktioniert ohne Fehler

---

### Phase 1.2: Scope Deviation Detection Integration
**Verantwortlich**: Backend Specialist + System Integrator  
**Geschätzte Zeit**: 30 Minuten  
**Dateien**: 
- `src/ct_dev_agent_orchestrator_mcp/services/session_service.py`
- `src/ct_dev_agent_orchestrator_mcp/services/opencode_api_client.py`

**Aufgabe 1.2.1**: Integration in opencode_api_client.py
- [ ] Import ScopeDeviationDetector in opencode_api_client.py
- [ ] Nach erfolgreichem send_message() Call:
  - [ ] Messages abrufen via get_messages()
  - [ ] ScopeDeviationDetector.detect_from_messages() aufrufen
  - [ ] Bei Detection: Logfire Warning loggen
  - [ ] Deviation in Response zurückgeben

**Code-Skelett** (opencode_api_client.py, nach send_message erfolg):
```python
from ct_dev_agent_orchestrator_mcp.utils.scope_deviation import ScopeDeviationDetector

# Nach erfolgreichem send_message:
messages = await self.get_messages(session_id)
deviation = ScopeDeviationDetector.detect_from_messages(messages)

if deviation:
    logfire.warn(
        "Scope deviation detected in session",
        session_id=session_id,
        deviation_type=deviation["type"],
        severity=deviation["severity"]
    )
    
    # Bei high/critical: Escalation
    if ScopeDeviationDetector.should_escalate(deviation):
        logfire.error(
            "Critical scope deviation requires escalation",
            session_id=session_id,
            deviation=deviation
        )

return deviation  # Wird in SessionInfo integriert
```

**Aufgabe 1.2.2**: Integration in SessionInfo Update
- [ ] In session_service.py: query_session() erweitern
- [ ] Nach Message-Send: Deviation Check ausführen
- [ ] SessionInfo.scope_deviation mit Detection-Result befüllen
- [ ] Bei CRITICAL/HIGH: Session Status auf CANCELLED setzen (Fail Fast)

**Erfolgs-Kriterium**: 
- Deviation wird erkannt und in SessionInfo zurückgegeben
- Logfire Warnings bei Detection
- Critical Deviations führen zu Session-Abbruch

---

### Phase 1.3: Test-Suite erstellen
**Verantwortlich**: QA Specialist  
**Geschätzte Zeit**: 45 Minuten  
**Datei**: `tests/test_opencode_api.py` (neu)

**Aufgabe 1.3.1**: Unit Tests für Scope Deviation
- [ ] Test: ScopeDeviationDetector.detect_scope_keywords()
  - [ ] Test mit "blocked" → erkennt BLOCKING_ISSUE
  - [ ] Test mit "beyond scope" → erkennt SCOPE_DRIFT
  - [ ] Test mit "unclear" → erkennt UNCLEAR_REQUIREMENTS
  - [ ] Test ohne Keywords → None
- [ ] Test: ScopeDeviationDetector._calculate_severity()
  - [ ] Test CRITICAL Keywords
  - [ ] Test HIGH für blocking
  - [ ] Test MEDIUM für unclear
  - [ ] Test LOW default
- [ ] Test: ScopeDeviationDetector.should_escalate()
  - [ ] Test TRUE für HIGH/CRITICAL
  - [ ] Test TRUE für BLOCKING unabhängig von Severity
  - [ ] Test FALSE für LOW/MEDIUM

**Aufgabe 1.3.2**: Integration Tests für OpenCode API
- [ ] Test: send_message() mit Deviation Detection
  - [ ] Mock aiohttp für OpenCode API Response
  - [ ] Mock Messages mit Deviation Keywords
  - [ ] Assert: Deviation detected und korrekt returned
- [ ] Test: send_message() ohne Deviation
  - [ ] Mock normale Messages
  - [ ] Assert: Keine Deviation, None returned
- [ ] Test: Session Abort bei Critical Deviation
  - [ ] Mock CRITICAL Deviation
  - [ ] Assert: Session Status = CANCELLED

**Aufgabe 1.3.3**: Validierungs-Tests
- [ ] Test: SessionInfo Model mit scope_deviation Field
  - [ ] Test JSON Serialization mit Deviation
  - [ ] Test JSON Serialization ohne Deviation (None)
- [ ] Test: Import von session.py funktioniert
  - [ ] Test: Optional korrekt importiert

**Test-Struktur**:
```python
"""Tests for OpenCode API integration and scope deviation detection."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from ct_dev_agent_orchestrator_mcp.utils.scope_deviation import ScopeDeviationDetector
from ct_dev_agent_orchestrator_mcp.models.session import SessionInfo
from ct_dev_agent_orchestrator_mcp.services.opencode_api_client import OpenCodeAPIClient


class TestScopeDeviationDetector:
    """Unit tests for ScopeDeviationDetector."""
    
    def test_detect_blocking_issue(self):
        """Test detection of blocking issues."""
        # Test implementation
        
    # Weitere Tests...


class TestOpenCodeAPIIntegration:
    """Integration tests for OpenCode API with deviation detection."""
    
    @pytest.mark.asyncio
    async def test_send_message_with_deviation(self):
        """Test send_message detects scope deviation."""
        # Test implementation with mocks
        
    # Weitere Tests...
```

**Erfolgs-Kriterium**: 
- Alle Tests grün
- Coverage >80% für opencode_api_client.py und scope_deviation.py
- `pytest tests/test_opencode_api.py -v --cov`

---

### Phase 1.4: Validierung & Review
**Verantwortlich**: Code Reviewer + Philosophical Reviewer  
**Geschätzte Zeit**: 30 Minuten

**Aufgabe 1.4.1**: Code Review
- [ ] Syntax Review: Code ist produktionsreif, fehlerfrei, wartbar
- [ ] Logic Review: Deviation Detection funktioniert wie erwartet
- [ ] Performance Review: Keine Performance-Einbußen durch Detection
- [ ] Security Review: Keine Sicherheitsprobleme

**Aufgabe 1.4.2**: Philosophical Review
- [ ] Einhaltung X^∞ Prinzipien: "Bei Abweichung zurück an Delegierenden"
- [ ] Fail Fast: Critical Deviations führen zu sofortigem Abbruch
- [ ] Observability: Logfire Integration korrekt
- [ ] Minimalismus: Keine Over-Engineering

**Aufgabe 1.4.3**: Funktionstest
- [ ] Build durchführen: `python3 -m pip install -e .`
- [ ] Server starten (Test-Environment)
- [ ] Manueller Test: spawn_agent mit Test-Task
- [ ] Test: send_message mit Deviation-Keywords
- [ ] Verify: Deviation wird erkannt und geloggt

**Erfolgs-Kriterium**: 
- Alle Reviews positiv
- Funktionstest erfolgreich
- Keine offenen Issues

---

## 🜄 Prüfung / Validation 🜄

### Cap-Selbstprüfung
- [ ] Verantwortung verstanden und akzeptiert
- [ ] Plan ist minimal und fokussiert (KISS)
- [ ] Keine Rückwärtskompatibilität erforderlich
- [ ] Fail Fast Prinzip umgesetzt

### Technische Prüfung
- [ ] Import-Fehler behoben
- [ ] Deviation Detection integriert
- [ ] Tests vorhanden und grün
- [ ] Coverage >80%
- [ ] Build erfolgreich
- [ ] Keine neuen Errors

### Ethik-Prüfung (Opportunitäts-Ethik)
- [ ] Keine anderen Tasks blockiert
- [ ] Keine Abhängigkeiten verletzt
- [ ] Schutz der Schwächsten: Agents können bei Problemen eskalieren
- [ ] Verantwortung klar: Deviation Detection ermöglicht bewusste Entscheidungen

---

## 🜄 Risiken / Nebenwirkungen 🜄

### Technische Risiken
1. **False Positives bei Deviation Detection**
   - Risiko: Zu aggressive Detection könnte legitime Work abbrechen
   - Mitigation: Severity-Level mit Thresholds, LOW ignorieren
   - Mitigation: Keyword-Liste sorgfältig kuratiert

2. **Performance Impact durch Message Analysis**
   - Risiko: Jeder send_message Call analysiert Messages
   - Mitigation: Detection nur auf Assistant Messages, effiziente Keyword-Suche
   - Monitoring: Logfire Performance Metrics

3. **Integration Breaking Changes**
   - Risiko: Änderungen könnten bestehende Session-Flows brechen
   - Mitigation: Backward-compatible Implementation (scope_deviation Optional)
   - Mitigation: Umfassende Tests

### Systemische Risiken
1. **Over-Alerting in Logfire**
   - Risiko: Zu viele Warnings könnten Signal/Noise Ratio verschlechtern
   - Mitigation: Nur MEDIUM+ severity loggen als Warning
   - Mitigation: LOW als Debug

2. **Incomplete Test Coverage**
   - Risiko: Unentdeckte Edge Cases
   - Mitigation: >80% Coverage Requirement
   - Mitigation: Integration Tests für kritische Flows

---

## 🜄 Aufgaben / To-Do 🜄

### Sofort (Kritisch)
- [ ] **FREIGABE DURCH AUCTOR EINHOLEN** ← BLOCKIERT WEITERE ARBEIT
- [ ] Nach Freigabe: Branch anlegen `feature/phase1-deviation-detection`
- [ ] Phase 1.1: Import Fix durchführen (Syntax Reviewer)
- [ ] Phase 1.1: Import testen

### Sequenziell nach Import Fix
- [ ] Phase 1.2: Deviation Detection integrieren (Backend Specialist)
- [ ] Phase 1.2: Integration testen
- [ ] Phase 1.3: Test Suite erstellen (QA Specialist)
- [ ] Phase 1.3: Tests ausführen und auf 100% grün bringen

### Abschluss
- [ ] Phase 1.4: Code Review (Code Reviewer)
- [ ] Phase 1.4: Philosophical Review (Philosophical Reviewer)
- [ ] Phase 1.4: Funktionstest durchführen
- [ ] Build & Restart durchführen
- [ ] Realistische Tests aus Usersicht
- [ ] Task in ct-task_mgmnt auf completed setzen
- [ ] Ptah informieren über Abschluss
- [ ] CHANGELOG.md aktualisieren
- [ ] Commit, Push, PR erstellen
- [ ] Deprecated/Test Files aufräumen

---

## 🜄 Zeitschätzung 🜄

| Phase | Geschätzte Zeit | Verantwortlich |
|-------|----------------|----------------|
| 1.1 Import Fix | 5 Min | Syntax Reviewer |
| 1.2 Integration | 30 Min | Backend Specialist |
| 1.3 Tests | 45 Min | QA Specialist |
| 1.4 Review | 30 Min | Reviewer Team |
| **Gesamt** | **~110 Min** | **Team** |

**Buffer**: +30 Min für unerwartete Issues  
**Total**: ~2,5 Stunden

---

## 🜄 Erfolgs-Kriterien 🜄

### Technisch
1. ✅ Import-Fehler behoben, SessionInfo importierbar
2. ✅ Scope Deviation Detection funktionsfähig
3. ✅ Tests vorhanden, alle grün, Coverage >80%
4. ✅ Build erfolgreich, Server startet
5. ✅ Manuelle Tests erfolgreich

### Prozessual
1. ✅ X^∞ Prozess eingehalten (Plan → Freigabe → Umsetzung → Review)
2. ✅ Alle Reviews positiv (Code + Philosophical)
3. ✅ Task in ct-task_mgmnt aktualisiert
4. ✅ Ptah informiert
5. ✅ Dokumentation aktualisiert

### Ethisch
1. ✅ Fail Fast Prinzip umgesetzt (Critical → Abort)
2. ✅ Observability erhöht (Logfire Integration)
3. ✅ Verantwortung klar (Deviation → Escalation)
4. ✅ Schutz der Agents (Können bei Problemen eskalieren)

---

## 🜄 Freigabe 🜄

**Status**: ⏳ WARTET AUF FREIGABE DURCH AUCTOR

**Freigabe-Kriterien**:
- [ ] Plan verstanden und akzeptiert
- [ ] Zeitrahmen akzeptabel
- [ ] Risiken akzeptabel
- [ ] Ressourcen verfügbar
- [ ] Keine Einwände

**Nach Freigabe**: Umsetzung beginnt gemäß Plan

---

**Erstellt**: 2025-10-01  
**Version**: 1.0  
**Autor**: GitHub Copilot CLI (Project Manager)  
**Delegation**: Von Auctor  
**Cap**: Planung
