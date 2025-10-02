## 🜄 Ziel 🜄
Implementierung der Cap & Delegation Responsibility Fields für vollständige X^∞ Verantwortungs-Nachvollziehbarkeit im Agent Spawning System.

## 🜄 Verantwortung 🜄
- **Cap-Quelle**: Auctor (offene Tasks umsetzen)
- **Task-ID**: a86d0e77-a8b8-4dcc-b854-cc27fe474c76
- **Delegiert an**: Project Manager → Backend Specialist (Implementation)

---

## 🔴 BREAKING CHANGE 🔴

**spawn_agent** MCP Tool benötigt jetzt **3 zusätzliche Pflichtfelder** für X^∞ Compliance:

1. **original_task**: Ursprungsaufgabe (task_id, title, description, requester, requested_at)
2. **cap_origin**: Autorität-Ursprung (ultimate_authority, original_scope, granted_at, grant_context)  
3. **delegation_context**: Aktueller Delegierender + Cap (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)

---

## Änderungen

### Models
- ✅ SessionInfo: +3 neue Pflichtfelder
- ✅ SpawnAgentRequest: +3 neue Pflichtfelder

### Service Layer
- ✅ spawn_agent: Verarbeitet Cap-Felder
- ✅ query_session: Gibt Cap-Felder zurück
- ✅ list_active_sessions: Enthält Cap-Felder

### MCP Tool
- ✅ Tool Schema mit Cap-Fields
- ✅ Handler Output erweitert

### Tests
- ✅ 20/20 Tests passing
- ✅ Helper Functions für Test-Daten

---

## Migration erforderlich

Alle spawn_agent Aufrufe müssen die 3 neuen Felder enthalten.
