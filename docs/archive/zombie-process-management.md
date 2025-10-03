# 🜄 Agent Orchestrator: Process Management Professionalisierung

## 🜄 Ziel
Elimination von Zombie-Prozessen und professionelles Prozessmanagement im Agent Orchestrator.

## 🜄 Kontext
- **Datum**: 2025-10-01
- **Git Status**: Modified server.py
- **Betroffene Komponente**: ct_dev-agent_orchestrator-mcp
- **Severity**: HIGH (Ressourcen-Leak, Systemstabilität)

## 🜄 Problem (Ist-Zustand)

### Symptome
- 3 Zombie-Prozesse (defunct) unter MCP Server PID 489837
- spawn_agent meldet SUCCESS obwohl Agent nicht erstellt wurde
- list_agents zeigt keine Agents trotz erfolgreicher spawn_agent Calls
- Sessions existieren in Memory aber nicht auf OpenCode Server

### Root Cause Analyse
1. **opencode_service.py:88-152 (start_agent)**
   - Verwendet subprocess.Popen() ohne ordentliches Cleanup
   - Keine process.wait() oder process.poll() zum "Ernten" beendeter Child-Prozesse
   - Health check failure setzt status=ERROR aber wirft keine Exception
   - Result: Agent wird als erfolgreich behandelt obwohl Server nicht läuft

2. **agent_manager.py (stop_agent)**
   - Fehlt oder ist unvollständig
   - Keine graceful shutdown Logik
   - Keine Zombie-Process Reaping

3. **session_service.py:73-163 (spawn_agent)**
   - Hardcodiert status=RUNNING ohne Validierung
   - Ignoriert agent.status von start_agent
   - TimeoutError handler generiert fake session_id mit FAILED status

4. **server.py:206-218 (spawn_agent handler)**
   - Meldet immer SUCCESS unabhängig von session_info.status
   - Keine Fehlerbehandlung für ERROR states

### Betroffene Dateien
- src/ct_dev_agent_orchestrator_mcp/services/opencode_service.py (start_agent, stop_agent)
- src/ct_dev_agent_orchestrator_mcp/services/agent_manager.py (create_agent, stop_agent)
- src/ct_dev_agent_orchestrator_mcp/services/session_service.py (spawn_agent)
- src/ct_dev_agent_orchestrator_mcp/server.py (spawn_agent handler)

## 🜄 Zielzustand (Requirements)

### Functional Requirements
1. Keine Zombie-Prozesse
2. Korrekte Status-Propagierung (ERROR states werden erkannt)
3. Graceful shutdown bei stop_agent
4. Automatic process reaping
5. spawn_agent meldet nur SUCCESS wenn Agent wirklich läuft

### Technical Requirements
1. Async subprocess management mit asyncio.create_subprocess_exec
2. Process registry mit PID tracking
3. Signal handler für graceful shutdown (SIGTERM, SIGINT)
4. Health check failure wirft Exception
5. Status validation in spawn_agent und server.py

## 🜄 Verantwortung
- **Planning**: Auctor (Cap)
- **Implementation**: Delegation an backend_specialist
- **Review**: Delegation an philosophical-code-reviewer
- **Testing**: Auctor

## 🜄 Next Steps
- [ ] Ptah für Context und Deep Research kontaktieren
- [ ] Root Cause Analyse durch Experten delegieren
- [ ] Zielzustand durch Architekten definieren lassen
- [ ] Peer Review durch Philosophical Reviewer
- [ ] Implementierungsplan durch Milestone Planer
- [ ] Tasks in ct_dev-task_mgmnt erstellen
- [ ] Freigabe durch Auctor abwarten
