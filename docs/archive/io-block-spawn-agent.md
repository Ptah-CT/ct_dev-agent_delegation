# 🜄 Issue: I/O Block in agent_orchestrator spawn_agent()

## 🜄 Ziel 🜄
MCP Server Timeout und I/O-Blockierung in spawn_agent() beheben.

## 🜄 Kontext 🜄
- **Projekt**: ct_dev-agent_orchestrator-mcp
- **Branch**: fix/asyncio-scope-error
- **Location**: /home/auctor/dev/ct_dev-agent_orchestrator-mcp
- **Datum**: 2025-10-02

## 🜄 Problem 🜄
MCP Server blockiert sofort nach Start mit massivem I/O-Wait:
- **Symptom**: 61-87% CPU I/O-Wait
- **Trigger**: spawn_agent() Tool-Call führt zu Timeout
- **Server-Status**: Disk Sleep (wchan: do_epoll_wait)
- **Reproduzierbar**: Tritt nach jedem Neustart sofort auf

## 🜄 Analyse 🜄

### Betroffene Dateien
- `src/ct_dev_agent_orchestrator_mcp/server.py` (call_tool handler)
- `src/ct_dev_agent_orchestrator_mcp/services/session_service.py` (spawn_agent)
- `src/ct_dev_agent_orchestrator_mcp/services/agent_manager.py` (create_agent)
- `src/ct_dev_agent_orchestrator_mcp/services/session_manager.py` (create_session)

### Call Chain
```
spawn_agent (MCP Tool)
  → SessionService.spawn_agent()
    → AgentManager.create_agent()  ← Blockierung hier?
      → opencode_service.create_session()
    → SessionManager.create_session()  ← Oder hier?
      → httpx.AsyncClient.post(server_url/session)
```

### Vermutete Ursachen (Ptah)
1. **httpx-Call blockiert**: `session_manager.create_session()` wartet auf OpenCode Server
   - Timeout: 30s konfiguriert
   - Mögliche Ursachen: OpenCode Server nicht gestartet, falsche URL, Netzwerk-Problem
   
2. **opencode_service blockiert**: `agent_manager.create_agent()` initialisiert OpenCode
   - Potentielle synchrone I/O-Calls
   - Fehlende await in async Chain

### Systemzustand
- **Zombie-Prozesse**: Gekillt (PIDs 174987, 180307)
- **Hängender find**: Gekillt (PID 179306, lief 12:45min)
- **Aktueller Server**: PID 185691 (neu gestartet, blockiert)

## 🜄 Nächste Schritte 🜄
- [ ] agent_manager.py vollständig analysieren
- [ ] session_manager.py httpx-Calls prüfen
- [ ] OpenCode Server Status/Config prüfen
- [ ] Blockierenden Call identifizieren
- [ ] Fix implementieren (async/await oder Timeout)
- [ ] Test durchführen

## 🜄 Verantwortung 🜄
- **Autor**: Claude (Project Manager)
- **Delegiert an**: Debug/Analysis Team
- **Status**: in_progress
- **Priorität**: critical

## 🜄 ROOT CAUSE IDENTIFIZIERT 🜄

**Blockierungspunkt**: `opencode_service.start_agent()`

Call Chain:
```
spawn_agent (MCP Tool)
  → SessionService.spawn_agent()
    → AgentManager.create_agent()
      → opencode_service.start_agent() ← **BLOCKIERT HIER**
        → process_manager.create_process(["opencode", "serve"])
        → Wartet auf Port-Detection aus stdout (max 5s)
        → _wait_for_health() (max 8s)
```

**Problem**: 
- `opencode serve` Prozess startet aber gibt keine Port-Info aus
- Port-Detection-Callback erhält kein "listening on http://..." 
- Timeout nach 5s → RuntimeError
- Parallel dazu: I/O-Wait durch Process-Polling

**Lösung**:
- [ ] Prüfe OpenCode-Installation und Version
- [ ] Debug: opencode serve manuell testen
- [ ] Alternative: Festen Port verwenden statt Port-Detection
- [ ] Timeout-Handling verbessern

## 🜄 Task Management 🜄
**Task-ID**: io-block-spawn-agent-fix  
**Projekt**: ct_dev-agent_orchestrator-mcp  
**Status**: in_progress  
**Priorität**: critical  
**Assigned**: Debug Team

## 🜄 Risiken 🜄
- Server-Crashes durch unhandled RuntimeError
- Race Conditions bei multi-spawn ohne Locks
- Ressourcen-Verschwendung durch hohe I/O-Wait
- OpenCode-Installation möglicherweise defekt