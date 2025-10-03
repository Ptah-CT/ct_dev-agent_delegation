## 🜄 Ziel 🜄
- Sicherstellen, dass ct_dev-agent_delegation-mcp stabile, wiederstartfähige OpenCode-Agenten bereitstellt.
- Verankern, dass Prozess- und Ressourcenüberwachung X^infty-Verantwortung sichtbar hält.

## 🜄 Kontext 🜄
### Überblick
Das ct_dev-agent_delegation-mcp System nutzt ein professionelles Process-Management, um OpenCode-Agent-Server zu starten, zu überwachen und kontrolliert zu stoppen. Delegations- und Agent-Lebenszyklen bleiben dadurch transparent und auditierbar.

### Architekturkomponenten
```
AgentManager  -> verwaltet Agent-Instanzen und Lifecycle
    |
    v
OpenCodeService -> startet/stoppt OpenCode Server, sammelt Metriken
    |
    v
ProcessManager -> Neustarts, Ressourcenüberwachung, Output Capture, Graceful Shutdown
```

## 🜄 Verantwortung 🜄
- Cap: Auctor (Mandat für Infrastruktur-Betrieb im X^infty-System).
- Umsetzung: Process Management Squad innerhalb des ct_dev Agent Delegation Teams.

## 🜄 Prüfung 🜄
- [ ] Neustart-Strategie getestet (max. 5 Versuche, Exponential Backoff).
- [ ] Ressourcenlimits validiert (Memory 1024 MB, CPU 80 % standardmäßig).
- [ ] Output-Capture aktiviert und geprüft (letzte 1000 Zeilen pro Stream).
- [ ] Graceful Shutdown Ablauf (SIGTERM → Wait → SIGKILL → Cleanup) simuliert.

## 🜄 Risiken / Nebenwirkungen 🜄
- Hohe Restart-Frequenz kann auf zugrunde liegende OpenCode-Probleme hinweisen.
- Ressourcengrenzen sind statisch; falsche Werte führen zu unnötigen Kills.
- Output-Buffer begrenzt auf 1000 Zeilen → detaillierte Logs extern sichern.

## 🜄 Aufgaben / To-Do 🜄
- [ ] Prozessmetriken regelmäßig in Logfire dashboarden.
- [ ] Restart- und Timeout-Parameter branch-spezifisch dokumentieren.
- [ ] ProcessManager Konfiguration in ct_dev-task_mgmnt hinterlegen.

---

### Kernfunktionen
1. **Automatische Neustarts** mit Exponential Backoff (max. 5 Versuche, 1 s Basis, 60 s Maximum).
2. **Ressourcenüberwachung** (CPU, Memory, Threads, offene Dateien, Verbindungen, Uptime).
3. **Ressourcenlimits** (Memory 1024 MB, CPU 80 %).
4. **Output Capture** (stdout/stderr, jeweils letzte 1000 Zeilen, Event-Callbacks).
5. **Graceful Shutdown** (SIGTERM → Wartezeit → SIGKILL → Cleanup).

### ProcessConfig Beispiel
```python
from ct_dev_agent_delegation_mcp.services.process_manager import ProcessConfig

config = ProcessConfig(
    auto_restart=True,
    max_restart_attempts=5,
    restart_delay_base=1.0,
    restart_delay_max=60.0,
    max_memory_mb=1024.0,
    max_cpu_percent=80.0,
    startup_timeout=30.0,
    shutdown_timeout=10.0,
    health_check_interval=30.0,
    capture_output=True
)
```

### AgentManager API Ausschnitte
```python
# Ressourcendaten
metrics = await agent_manager.get_agent_metrics(agent_id)

# Output abrufen
output = await agent_manager.get_agent_output(agent_id, lines=100)

# Agent neu starten
success = await agent_manager.restart_agent(agent_id)

# Prozesszustände einsehen
states = agent_manager.get_process_states()
```

### OpenCodeService API Ausschnitte
```python
metrics = await opencode_service.get_agent_metrics(agent)
output = await opencode_service.get_agent_output(agent, lines=200, include_stderr=True)
states = opencode_service.get_all_process_states()
```

### Monitoring
- Health Checks alle 30 Sekunden (Prozesszustand, HTTP-Endpoint, Ressourcenverbrauch).
- Metriken via Logfire und interne Dashboards verfügbar.
- Alerts empfohlen bei Restart-Serien oder Ressourcenlimit-Verletzungen.
