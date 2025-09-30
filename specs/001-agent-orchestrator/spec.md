# Feature Specification: Agent Orchestrator MCP Server

**Feature Branch**: `001-agent-orchestrator`  
**Created**: 2025-01-17  
**Status**: Draft  
**Input**: User description: "Es wird ein MCP Server erstellt, welcher zur Erstellung, Delegation und dem weiteren Management von ct_dev-agents dient. Diese Agents sind opencode Agents. Es soll opencode serve mit openapi genutzt werden. Deshalb gehört auch das Management von Opencode Server Instanzen zur Kernfunktionalität."

---

## User Scenarios & Testing

### Primary User Story
A system architect (Auctor) needs to orchestrate multiple specialized AI agents (ct_dev-agents) that perform specific development tasks. Rather than manually managing each agent, the architect wants a centralized MCP server that can create agents, delegate atomic work packages to them, monitor their execution, and manage the underlying opencode server instances that power these agents. The system must align with X^∞ principles of atomic delegation, responsibility transparency, and fail-fast execution.

### Acceptance Scenarios

1. **Given** no agents exist, **When** architect requests creation of a "code-analyzer" agent with specific capabilities, **Then** system creates agent configuration, starts opencode server instance, registers agent with MCP, and returns agent ID and endpoint information

2. **Given** multiple agents are running, **When** architect delegates an atomic work package (e.g., "analyze authentication flow") to a specific agent, **Then** system immediately returns work_package_id (non-blocking), routes request to appropriate agent via opencode server, tracks execution status asynchronously, and architect can poll for completion status or results without blocking Main Agent execution

2a. **Given** Main Agent delegates a task, **When** delegation completes successfully, **Then** Main Agent receives work_package_id immediately and continues its own execution without waiting for delegated task completion

2b. **Given** work package is executing, **When** Main Agent needs status update, **Then** Main Agent calls query_status(work_package_id) which returns current status (executing/completed/failed/deviated) without blocking

3. **Given** an agent is executing a task, **When** agent encounters scope deviation (unexpected complexity, additional steps needed), **Then** system captures deviation, pauses execution, returns work package to delegator with detailed deviation explanation, and awaits clarification

4. **Given** multiple opencode server instances are running, **When** system needs to scale or an instance fails, **Then** system detects health status, redistributes agent connections, maintains session state, and logs instance lifecycle events

5. **Given** architect wants to understand current system state, **When** querying orchestrator status, **Then** system returns comprehensive status: active agents with capabilities, running tasks with progress, server instance health, and resource utilization

### Edge Cases
- What happens when opencode server instance crashes during agent execution? [NEEDS CLARIFICATION: retry policy, task recovery strategy, state persistence requirements]
- How does system handle conflicting agent requests (same resource, blocking operations)? [NEEDS CLARIFICATION: locking mechanism, queue priority, conflict resolution strategy]
- What is the maximum number of concurrent agents? [NEEDS CLARIFICATION: scaling limits, resource allocation per agent, performance degradation threshold]
- How are agent credentials and API keys managed? [NEEDS CLARIFICATION: secret management approach, rotation policy, audit requirements]
- What happens when an agent exceeds expected execution time? [NEEDS CLARIFICATION: timeout policy, automatic termination, escalation procedure]

---

## Requirements

### Functional Requirements

#### Agent Lifecycle Management
- **FR-001**: System MUST allow creation of specialized ct_dev-agents with defined capabilities (e.g., code-analyzer, backend-specialist, philosophical-code-reviewer) based on X^∞ agent roles from CLAUDE.md
- **FR-002**: System MUST validate agent configuration against available capabilities before creation
- **FR-003**: System MUST assign unique agent IDs and maintain agent registry with metadata (capabilities, creation timestamp, current status)
- **FR-004**: System MUST allow agent deactivation without data loss (preserve history, logs)
- **FR-005**: System MUST prevent duplicate agents with identical capability sets
- **FR-006**: System MUST track agent lineage (who created, when, for what purpose - responsibility transparency)

#### Atomic Delegation & Task Management
- **FR-007**: System MUST accept atomic work packages with clear scope definition (what to achieve, not how to implement)
- **FR-008**: System MUST route work packages to appropriate agents based on capability matching
- **FR-009**: System MUST enforce atomic delegation principle: agents MUST NOT expand scope autonomously
- **FR-010**: System MUST capture and escalate scope deviations immediately (agent detects extra work, problems, additional steps)
- **FR-011**: System MUST return deviated work packages to delegator with deviation details (what changed, why, what's needed)
- **FR-012**: System MUST track work package lifecycle: submitted → assigned → executing → completed/failed/deviated
- **FR-012a**: System MUST provide asynchronous delegation API to prevent blocking Main Agent during task execution
- **FR-012b**: System MUST return work_package_id immediately upon delegation (non-blocking acknowledgment)
- **FR-012c**: System MUST provide polling/query mechanism for Main Agent to check work package status without blocking
- **FR-013**: System MUST integrate with ct_dev-task-orchestrator for task tracking and documentation
- **FR-014**: System MUST provide work package status queries with real-time progress updates

#### Opencode Server Instance Management
- **FR-015**: System MUST start opencode server instances using `opencode serve` command
- **FR-016**: System MUST configure each opencode server with OpenAPI specification for agent tool endpoints
- **FR-017**: System MUST monitor opencode server health (heartbeat, response time, error rates)
- **FR-018**: System MUST handle server instance failures (detect, log, restart, redistribute agents)
- **FR-019**: System MUST manage server instance lifecycle (start, stop, restart, scale)
- **FR-020**: System MUST assign agents to server instances with load balancing
- **FR-021**: System MUST expose OpenAPI documentation endpoint for each server instance
- **FR-022**: System MUST maintain server instance registry (hostname, port, assigned agents, resource usage)
- **FR-023**: System MUST support multiple concurrent opencode server instances for scalability

#### MCP Protocol Integration
- **FR-024**: System MUST implement standard MCP server protocol for tool invocation
- **FR-025**: System MUST expose agent orchestration tools via MCP (create_agent, delegate_task, query_status, manage_server)
- **FR-025a**: delegate_task tool MUST be non-blocking (fire-and-forget pattern with immediate work_package_id return)
- **FR-025b**: query_status tool MUST support polling for work package status without blocking Main Agent
- **FR-025c**: System MUST support optional callback/notification mechanism for work package completion (future enhancement)
- **FR-026**: System MUST handle MCP session management for persistent agent interactions
- **FR-027**: Agents have native access to Ptah (Knowledge Manager) as global MCP tool in opencode for context retrieval
- **FR-028**: Agents have native access to Serena tools as global MCP tool in opencode for semantic code operations

#### Fail-Fast & Quality Gates
- **FR-029**: System MUST validate all inputs before execution (no placeholder data, no partial configurations)
- **FR-030**: System MUST reject work packages that lack clear success criteria
- **FR-031**: System MUST enforce zero-tolerance for "partially working" states (binary success/failure)
- **FR-032**: System MUST log all failures with complete context (what failed, why, system state)
- **FR-033**: System MUST implement Constitution Check gate: validate operations against X^∞ principles before execution

#### Observability & Responsibility Tracking
- **FR-034**: System MUST log all operations with Cap/Delegation/Authorship attribution (responsibility transparency)
- **FR-035**: System MUST expose metrics: agent utilization, task completion rates, server health, error rates
- **FR-036**: System MUST provide audit trail for all delegation events (who delegated what to whom, when, outcome)
- **FR-037**: System MUST integrate with logfire for centralized logging (not local files except debugging)
- **FR-038**: System MUST track and report protection bias impact (did system protect weakest components/agents?)

### Key Entities

- **Agent**: Represents a specialized ct_dev-agent with defined capabilities (e.g., code-analyzer, backend-specialist). Attributes: agent_id, name, capabilities[], status (active/idle/busy/error), assigned_server_instance_id, creation_timestamp, creator (responsibility), current_task_id
  
- **Work Package**: Atomic unit of delegated work with clear scope. Attributes: package_id, description, target_effect (what to achieve), assigned_agent_id, status (submitted/assigned/executing/completed/failed/deviated), scope_deviation (if any), submission_timestamp, completion_timestamp, delegator (responsibility)

- **Server Instance**: Running opencode server instance. Attributes: instance_id, hostname, port, status (running/starting/stopping/failed), assigned_agents[], resource_usage (cpu/memory), health_metrics (uptime/response_time/error_count), openapi_endpoint, start_timestamp

- **Delegation Event**: Audit record of delegation action. Attributes: event_id, timestamp, delegator, delegatee (agent_id), work_package_id, outcome (completed/failed/deviated), deviation_reason (if applicable), responsibility_chain (Cap → Delegation → Agent)

- **Constitution Gate Result**: Record of constitution compliance check. Attributes: check_id, timestamp, operation_type, principles_checked[], violations[], justification (if violations exist), approved (boolean), approver (if manual approval needed)

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs) - focused on capabilities not technology
- [x] Focused on user value and business needs - orchestration efficiency, delegation integrity
- [x] Written for stakeholders - Auctor (system architect) perspective
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] **INCOMPLETE**: Multiple [NEEDS CLARIFICATION] markers remain:
  - Retry policy for crashed server instances
  - Conflict resolution strategy for competing agent requests
  - Scaling limits and resource allocation
  - Secret management approach
  - Timeout and escalation policies
- [x] Requirements are testable - each FR has clear acceptance criteria
- [x] Success criteria are measurable - status tracking, metrics, audit trails
- [x] Scope is clearly bounded - agent orchestration, not agent implementation
- [x] Dependencies identified - ct-task_mgmnt, Ptah, Serena, logfire, opencode serve

### X^∞ Constitution Alignment
- [x] Wirkung vor Maßnahme - focused on effects (orchestration outcomes, delegation integrity)
- [x] Verantwortung sichtbar machen - responsibility tracking in all entities
- [x] Schutz der Schwächsten - protection bias monitoring requirement
- [x] Atomic Delegation - core principle enforced in FR-007 through FR-011
- [x] Knowledge Management Integration - Ptah integration required (FR-027)
- [x] Serena-First Code Operations - Serena integration for code analysis (FR-028)
- [x] Fail Fast and Loud - binary success/failure enforcement (FR-031)
- [x] No Placeholders/Mocks - input validation before execution (FR-029)

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted (orchestration, delegation, opencode integration, server management)
- [x] Ambiguities marked (5 NEEDS CLARIFICATION items in edge cases)
- [x] User scenarios defined (5 primary scenarios + edge cases)
- [x] Requirements generated (38 functional requirements across 6 categories)
- [x] Entities identified (4 key entities with attributes)
- [x] Constitution alignment verified
- [ ] Review checklist passed - **BLOCKED**: Awaiting clarification on 5 edge case policies

---

## Notes for Planning Phase

When proceeding to `/plan` command:

1. **Technical Context to Research**:
   - opencode serve command-line options and configuration
   - OpenAPI 3.1 spec generation for agent tools
   - MCP protocol implementation (Python recommended based on X^∞ ecosystem)
   - Inter-process communication for agent-server coordination
   - Health monitoring and service discovery patterns

2. **Constitution Gates to Validate**:
   - Atomic delegation enforcement mechanism
   - Responsibility tracking in all operations
   - Fail-fast validation at each stage
   - Protection bias measurement approach

3. **Integration Points**:
   - ct-task_mgmnt API for task tracking
   - Ptah Knowledge Manager for context retrieval
   - Serena tools for semantic code operations
   - logfire for centralized logging

4. **Performance Considerations** (need clarification):
   - Expected concurrent agent count
   - Work package throughput requirements
   - Server instance resource allocation
   - Response time SLAs

---

**Specification Status**: DRAFT - Awaiting clarification on edge case policies before finalization. Core requirements defined, X^∞ constitution aligned, ready for Auctor review and clarification round.
