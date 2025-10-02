# Professional Process Management

## Übersicht

Das ct_dev-agent_orchestrator-mcp System verwendet jetzt ein professionelles Process Management System für die Verwaltung von OpenCode Agent-Servern. Dies bietet erweiterte Funktionen wie automatische Neustarts, Ressourcenüberwachung und graceful Shutdown.

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────┐
│                    AgentManager                          │
│  - Verwaltet Agent-Instanzen                            │
│  - Koordiniert Lifecycle                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  OpenCodeService                         │
│  - Startet/Stoppt OpenCode Server                       │
│  - Health Checks & Metrics                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  ProcessManager                          │
│  - Professionelle Prozessverwaltung                     │
│  - Automatische Neustarts                               │
│  - Ressourcenüberwachung (CPU, Memory)                  │
│  - Output Capture & Streaming                           │
│  - Graceful Shutdown                                     │
└─────────────────────────────────────────────────────────┘
```

## Features

### 1. Automatische Neustarts mit Exponential Backoff

Prozesse werden bei unerwarteten Fehlern automatisch neu gestartet:

- **Max Restarts**: 5 Versuche (konfigurierbar)
- **Base Delay**: 1 Sekunde
- **Max Delay**: 60 Sekunden
- **Strategie**: Exponential Backoff (2^n * base_delay)

```python
# Beispiel: Restart-Verzögerungen
Versuch 1: 1s
Versuch 2: 2s
Versuch 3: 4s
Versuch 4: 8s
Versuch 5: 16s
```

### 2. Ressourcenüberwachung

Kontinuierliche Überwachung von Prozess-Metriken:

- **CPU-Nutzung**: Prozent-Auslastung
- **Memory-Nutzung**: MB und Prozent
- **Thread-Anzahl**: Aktive Threads
- **Open Files**: Anzahl offener Dateien
- **Connections**: Anzahl aktiver Verbindungen
- **Uptime**: Laufzeit in Sekunden

### 3. Ressourcenlimits

Automatische Erkennung von Grenzwert-Überschreitungen:

- **Memory Limit**: 1024 MB pro Agent (konfigurierbar)
- **CPU Limit**: 80% (konfigurierbar)

### 4. Output Capture

Alle Prozess-Ausgaben werden erfasst:

- **STDOUT**: Standard-Ausgabe (letzte 1000 Zeilen)
- **STDERR**: Fehler-Ausgabe (letzte 1000 Zeilen)
- **Callbacks**: Event-basierte Verarbeitung

### 5. Graceful Shutdown

Kontrolliertes Herunterfahren von Prozessen:

1. **SIGTERM**: Graceful termination signal
2. **Wait**: Wartezeit (10 Sekunden default)
3. **SIGKILL**: Force kill bei Timeout
4. **Cleanup**: Resource cleanup

## Konfiguration

### ProcessConfig

```python
from ct_dev_agent_orchestrator_mcp.services.process_manager import ProcessConfig

config = ProcessConfig(
    # Restart Policy
    auto_restart=True,
    max_restart_attempts=5,
    restart_delay_base=1.0,
    restart_delay_max=60.0,
    
    # Resource Limits
    max_memory_mb=1024.0,
    max_cpu_percent=80.0,
    
    # Timeouts
    startup_timeout=30.0,
    shutdown_timeout=10.0,
    health_check_interval=30.0,
    
    # Process Options
    capture_output=True,
    working_directory=None,
    environment=None
)
```

## API

### AgentManager

#### Metrics abrufen

```python
# Get resource metrics for an agent
metrics = await agent_manager.get_agent_metrics(agent_id)
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_mb']} MB")
print(f"Uptime: {metrics['uptime_seconds']}s")
print(f"Restarts: {metrics['restart_count']}")
```

#### Output abrufen

```python
# Get recent process output
output = await agent_manager.get_agent_output(agent_id, lines=100)
print("STDOUT:", output['stdout'])
print("STDERR:", output['stderr'])
```

#### Agent neu starten

```python
# Manually restart an agent
success = await agent_manager.restart_agent(agent_id)
if success:
    print("Agent restarted successfully")
```

#### Process States abrufen

```python
# Get all process states
states = agent_manager.get_process_states()
for agent_id, state in states.items():
    print(f"{agent_id}: {state['state']} (PID: {state['pid']})")
```

### OpenCodeService

#### Agent-Metriken

```python
# Get metrics directly from OpenCodeService
metrics = await opencode_service.get_agent_metrics(agent)
```

#### Agent-Output

```python
# Get output with custom options
output = await opencode_service.get_agent_output(
    agent, 
    lines=200, 
    include_stderr=True
)
```

#### Process States

```python
# Get all managed process states
states = opencode_service.get_all_process_states()
```

## Monitoring

### Health Checks

Automatische Health Checks alle 30 Sekunden:

1. **Process State**: Läuft der Prozess noch?
2. **HTTP Endpoint**: Antwortet der Server?
3. **Resource Usage**: Sind Limits eingehalten?

### Metrics Collection

Kontinuierliche Erfassung von Metriken alle 5 Sekunden:

- CPU & Memory Usage
- Thread Count
- Open Files & Connections
- Uptime

### Logging

Alle relevanten Events werden mit Logfire protokolliert:

```python
logfire.info("Process started", pid=123)
logfire.warning("Process exceeds memory limit", memory_mb=1500)
logfire.error("Process died unexpectedly")
```

## Troubleshooting

### Problem: Agent startet nicht

**Symptome**: Agent bleibt in STARTING state

**Lösung**:
1. Prüfe Output: `await agent_manager.get_agent_output(agent_id)`
2. Prüfe Logs: Suche nach Fehler-Meldungen
3. Prüfe System-Ressourcen: Genug RAM/CPU verfügbar?

### Problem: Agent crasht wiederholt

**Symptome**: Viele Restarts in kurzer Zeit

**Lösung**:
1. Prüfe Metriken: `await agent_manager.get_agent_metrics(agent_id)`
2. Prüfe Memory-Limit: Eventuell erhöhen
3. Prüfe Output: Nach Error-Patterns suchen

### Problem: Graceful Shutdown funktioniert nicht

**Symptome**: Prozesse werden force-killed

**Lösung**:
1. Erhöhe `shutdown_timeout` in ProcessConfig
2. Prüfe ob Prozess SIGTERM handled
3. Prüfe ob blocking operations vorhanden

## Best Practices

### 1. Resource Limits setzen

Immer sinnvolle Limits definieren:

```python
config = ProcessConfig(
    max_memory_mb=1024.0,  # 1GB
    max_cpu_percent=80.0   # 80%
)
```

### 2. Output Monitoring

Nutze Callbacks für Echtzeit-Monitoring:

```python
def on_error(line: str):
    if "FATAL" in line:
        send_alert(line)

managed_process.on_error = on_error
```

### 3. Graceful Shutdown

Stelle sicher, dass cleanup immer läuft:

```python
try:
    # Work
    pass
finally:
    await agent_manager.stop()
```

### 4. Metrics regelmäßig prüfen

Implementiere Monitoring-Dashboard:

```python
async def monitor_loop():
    while True:
        states = agent_manager.get_process_states()
        for agent_id, state in states.items():
            if state['memory_mb'] > 800:
                logfire.warning(f"High memory usage: {agent_id}")
        await asyncio.sleep(60)
```

## Performance

### Overhead

Das Process Management System hat minimalen Overhead:

- **Startup**: +0-2s durch robuste Initialisierung
- **Runtime**: <1% CPU für Monitoring
- **Memory**: ~10MB pro verwalteten Prozess

### Skalierung

Das System skaliert gut:

- **5 Agents**: Standard-Konfiguration
- **10 Agents**: Möglich mit erhöhtem RAM
- **20+ Agents**: Erfordert Resource Tuning

### Optimierung

Für bessere Performance:

1. Reduziere `health_check_interval`
2. Deaktiviere Output Capture bei stabilen Prozessen
3. Erhöhe System-Ressourcen

## Migration

### Von altem System

Wenn du vom alten subprocess-basierten System migrierst:

**Alt**:
```python
process = subprocess.Popen(cmd)
agent.pid = process.pid
```

**Neu**:
```python
managed_process = await process_manager.create_process(
    process_id=agent_id,
    command=cmd,
    config=process_config
)
agent.pid = managed_process.pid
```

### Breaking Changes

- `psutil.Process` wird nicht mehr direkt verwendet
- Process PIDs sollten nicht mehr direkt manipuliert werden
- Shutdown erfordert `await process_manager.stop()`

## Roadmap

### Geplante Features

- [ ] Process Groups für koordiniertes Management
- [ ] Custom Health Check Callbacks
- [ ] Metrics Export (Prometheus)
- [ ] Process Snapshots & Restore
- [ ] Container Support (Docker)
- [ ] Advanced Resource Policies (Cgroups)

## Support

Bei Fragen oder Problemen:

1. Prüfe die Logs mit Logfire
2. Nutze `get_agent_metrics()` für Diagnostik
3. Aktiviere Debug-Logging für Details

## Siehe auch

- [OpenCode Service](opencode_service.py)
- [Agent Manager](agent_manager.py)
- [Process Manager](process_manager.py)
