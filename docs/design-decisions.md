# Design Decisions and Rationale

This document captures key architectural decisions and their rationale.

## Decision Log

### DD-001: API-First Approach (2025-01-30)

**Status**: ✓ Accepted

**Context**: 
Agent Orchestrator needs information about available agents, models, and configurations. Two approaches:
1. Read from file system (.claude/agents/, config files)
2. Query OpenCode Server API

**Decision**: Use OpenCode Server API exclusively (HTTP/OpenAPI)

**Rationale**:
- **Single Source of Truth**: OpenCode is the authoritative source
- **No Sync Issues**: No risk of stale data or race conditions
- **Dynamic Updates**: Changes in OpenCode immediately available
- **Future-Proof**: Works with remote OpenCode servers
- **Separation of Concerns**: Orchestrator doesn't need file system knowledge

**Consequences**:
- ✅ Always up-to-date information
- ✅ Works with any OpenCode version/config
- ✅ Simpler code (no file parsing)
- ⚠️ Network latency (acceptable for control plane)
- ⚠️ Dependency on API availability (mitigated by health checks)

**Alternatives Rejected**:
- File-based discovery: Would create sync problems
- CLI-based (opencode agents): Parsing overhead, version dependent
- Hybrid approach: Adds complexity without benefits

---

### DD-002: Session = Agent Instance (2025-01-30)

**Status**: ✓ Accepted

**Context**:
Need to represent running agents. Options:
1. Create custom Agent abstraction
2. Use OpenCode Sessions directly
3. Hybrid model with wrapper

**Decision**: Use OpenCode Sessions as-is, expose session_id to PM Agent

**Rationale**:
- **Native Fit**: OpenCode Sessions are designed for agent tasks
- **Rich State**: Sessions already have messages, files, permissions
- **Children Support**: Sessions can have sub-sessions
- **No Translation**: Direct mapping, less code
- **Transparency**: PM Agent sees actual OpenCode state

**Consequences**:
- ✅ Simple, direct implementation
- ✅ Full OpenCode functionality available
- ✅ No impedance mismatch
- ⚠️ PM Agent needs to understand session lifecycle
- ⚠️ Tied to OpenCode session model

**Alternatives Rejected**:
- Custom abstraction: Unnecessary complexity, loses information
- Polling-based status: Already have event system in OpenCode
- Task queue model: Sessions already provide this

---

### DD-003: Multi-Instance Strategy (2025-01-30)

**Status**: ✓ Accepted

**Context**:
How to handle multiple concurrent agents? Options:
1. Single OpenCode instance with queue
2. Multiple OpenCode instances (one per agent)
3. Pre-spawned pool of instances

**Decision**: Multiple OpenCode instances (5-10 max, configurable)

**Rationale**:
- **True Parallelism**: Real concurrent execution
- **Isolation**: Agent failures don't affect others
- **Resource Control**: Can limit total resources
- **Load Distribution**: Better CPU/Memory utilization
- **Scalability**: Linear scaling up to max_agents

**Consequences**:
- ✅ Better performance for concurrent work
- ✅ Failure isolation
- ✅ Predictable resource usage
- ⚠️ More memory (200-500MB per instance)
- ⚠️ More processes to manage
- ⚠️ Port management complexity

**Configuration**:
```python
MAX_AGENTS = 10  # Configurable
BASE_PORT = 8000  # Starting port
```

**Alternatives Rejected**:
- Single instance: Serializes agent work, bad for concurrency
- One-per-request: Too slow (startup time ~2-5s)
- Dynamic scaling: Over-engineering for current needs

---

### DD-004: Minimal State Caching (2025-01-30)

**Status**: ✓ Accepted

**Context**:
What state should Agent Orchestrator cache? Options:
1. Cache everything (full mirror)
2. Cache nothing (always query)
3. Minimal cache (only mapping)

**Decision**: Cache only session_id ↔ server_url mapping

**Rationale**:
- **Always Fresh**: No stale data problems
- **Simple**: No cache invalidation logic
- **Low Latency**: Session mapping is O(1)
- **Fail-Safe**: If cache lost, can recover from OpenCode

**Consequences**:
- ✅ No sync bugs
- ✅ Simple implementation
- ✅ Always accurate data
- ⚠️ More API calls (acceptable, control plane)
- ⚠️ Slightly higher latency per operation

**What We Cache**:
```python
_sessions: Dict[str, Dict[str, Any]]  # session_id -> {server_url, metadata}
_server_mapping: Dict[str, str]       # session_id -> server_url
```

**What We DON'T Cache**:
- Session status (query live)
- Messages (query live)
- Agent definitions (query live)
- Configuration (query live)

**Alternatives Rejected**:
- Full mirroring: Complex, sync issues, memory overhead
- Complete stateless: Can't route requests without mapping

---

### DD-005: Transparent Error Propagation (2025-01-30)

**Status**: ✓ Accepted

**Context**:
How to handle OpenCode errors? Options:
1. Abstract/map to generic errors
2. Pass through with context
3. Hide and retry automatically

**Decision**: Pass through OpenCode errors with added context

**Rationale**:
- **Full Information**: PM Agent gets complete picture
- **Better Debugging**: Original error preserved
- **Flexible Handling**: PM Agent can decide retry strategy
- **No Information Loss**: All details available

**Consequences**:
- ✅ Maximum information for PM Agent
- ✅ Better debugging experience
- ✅ PM Agent can handle specifically
- ⚠️ PM Agent needs to understand some OpenCode concepts
- ⚠️ Error messages are OpenCode-specific

**Error Format**:
```python
{
    "success": false,
    "error": {
        "type": "OpenCodeError",
        "message": "Session not found",
        "session_id": "abc123",
        "server_url": "http://localhost:8000",
        "original_error": {...}  # Original OpenCode response
    }
}
```

**Alternatives Rejected**:
- Generic error codes: Loses context, harder to debug
- Auto-retry: PM Agent might have better strategy
- Silent failures: Unacceptable for reliability

---

### DD-006: Fail-Fast Philosophy (2025-01-30)

**Status**: ✓ Accepted

**Context**:
Retry strategy for OpenCode API failures? Options:
1. Extensive retries (10+)
2. Minimal retries (2-3)
3. No retries (fail immediately)

**Decision**: Fail-fast with 2-3 retries max, short timeouts

**Rationale**:
- **Quick Feedback**: PM Agent knows immediately
- **PM Agent Control**: Better positioned to decide
- **Resource Efficiency**: Don't waste time on dead servers
- **Clear Failures**: Better than silent hangs

**Configuration**:
```python
API_TIMEOUT = 30s        # Default timeout
API_RETRY_COUNT = 2      # Max retries
RETRY_BACKOFF = 1s       # Backoff between retries
HEALTH_CHECK_TIMEOUT = 5s  # Health check timeout
```

**Consequences**:
- ✅ Fast failure detection
- ✅ PM Agent gets timely errors
- ✅ No hidden retries consuming resources
- ⚠️ PM Agent needs error handling logic
- ⚠️ Transient errors might not be retried enough

**Alternatives Rejected**:
- Long retries: Wastes time, PM Agent waits too long
- Exponential backoff: Over-engineering for control plane
- Circuit breaker: Good for future, not needed initially

---

## Future Decisions Needed

### FD-001: Session Pooling
**Question**: Should we reuse idle sessions or always create new ones?
**Status**: Deferred - Start with always-new, optimize if needed

### FD-002: Event Streaming
**Question**: Should we stream OpenCode events to PM Agent?
**Status**: Deferred - Polling sufficient initially, SSE for future

### FD-003: Configuration Management
**Question**: Should Orchestrator modify OpenCode config (PATCH /config)?
**Status**: Deferred - Start read-only, add if use case emerges

### FD-004: Authentication
**Question**: How to handle OpenCode authentication?
**Status**: Deferred - Local servers don't need auth initially

### FD-005: Distributed Orchestrator
**Question**: Multiple Orchestrator instances sharing OpenCode servers?
**Status**: Out of scope - Single Orchestrator sufficient for MVP

---

## Metrics and Validation

To validate these decisions, we track:

1. **API Latency**: Should be <100ms p95 for control operations
2. **Cache Hit Rate**: N/A (minimal caching by design)
3. **Error Rate**: Should be <1% under normal operation
4. **Resource Usage**: <500MB RAM per OpenCode instance
5. **Startup Time**: <5s per OpenCode instance
6. **Concurrent Agents**: Should handle 10 concurrent without degradation

---

## Review Schedule

These decisions should be reviewed:
- After MVP deployment (3 months)
- If OpenCode API changes significantly
- If performance issues arise
- If new use cases emerge
