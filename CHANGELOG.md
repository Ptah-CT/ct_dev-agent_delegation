# Changelog

## [Unreleased]

### BREAKING CHANGES - Project & Terminology Refactoring
- **Project Renamed**: `ct_dev-agent_orchestrator-mcp` → `ct_dev-agent_delegation-mcp`
  - Package name: `ct_dev_agent_orchestrator_mcp` → `ct_dev_agent_delegation_mcp`
  - All imports updated across 25+ Python files
  - Philosophy alignment: "Delegation" better represents X^∞ Cap-Transfer principles than "Session"

- **Model Renames** (Session → Delegation terminology):
  - `SessionStatus` → `DelegationStatus`
  - `SpawnAgentRequest` → `SpawnDelegationRequest`
  - `SessionInfo` → `DelegationInfo`
  - `models/session.py` → `models/delegation.py`

- **Service Renames**:
  - `SessionService` → `DelegationService`
  - `services/session_service.py` → `services/delegation_service.py`

- **MCP Tool Renames** (Breaking API Changes):
  - `list_agents` → `list_running_delegations` (lists active delegation instances)
  - `list_opencode_agents` → `list_available_agent_roles` (lists available agent roles from OpenCode)

- **Removed Duplicate Tools**:
  - Removed duplicate `get_agent_capabilities` tool definition (conflicted with OpenCode integration)

### Changed
- Architecture terminology: "session-based" → "delegation-based" throughout documentation
- Task integration reference: `ct_dev-task_orchestrator` → `ct_dev-task_mgmnt`
- All test files updated with new import paths and class names
- README.md completely rewritten with delegation-focused terminology
- File structure documentation updated to reflect new naming

### Migration Guide
**For MCP Clients using this server:**

1. **Update tool calls**:
   ```python
   # Old (deprecated):
   list_agents()  # Lists running instances
   list_opencode_agents()  # Lists available roles
   
   # New (current):
   list_running_delegations()  # Lists running instances  
   list_available_agent_roles()  # Lists available roles
   ```

2. **Update package imports** (if importing directly):
   ```python
   # Old:
   from ct_dev_agent_orchestrator_mcp.models.session import SessionInfo
   from ct_dev_agent_orchestrator_mcp.services.session_service import SessionService
   
   # New:
   from ct_dev_agent_delegation_mcp.models.delegation import DelegationInfo
   from ct_dev_agent_delegation_mcp.services.delegation_service import DelegationService
   ```

3. **No functional changes**: All delegation logic remains identical, only naming changed

### Fixed
- Syntax error after duplicate tool removal (missing comma in tool definitions)
- Import paths in all test files updated to new package structure

### Technical Details
- Database schema already correct (uses "delegations" table)
- All 25+ Python files updated systematically
- Complete test suite migration completed
- Zero functional regressions - pure renaming refactor

### Added - Phase 3: OpenCode Integration Service Layer & MCP Tools
- **OpenCode Dynamic Agent/Model Discovery**: New MCP tools for runtime agent and model discovery
  - `list_opencode_agents`: Lists all available OpenCode agents with configurations
  - `list_opencode_models`: Lists all available models grouped by provider
  - Force refresh parameter support for cache invalidation
  - Automatic caching with OpenCodeClient integration
- **Enhanced Session Manager**: Extended OpenCodeSessionManager with Phase 3 features
  - `create_session` now accepts optional `agent` and `model` parameters for dynamic agent/model selection
  - `get_config()`: Retrieve current OpenCode server configuration
  - `update_config()`: Update OpenCode configuration at runtime
  - `list_commands()`: List available slash commands
  - `execute_command()`: Execute slash commands within sessions
- **OpenCodeClient**: New centralized client for OpenCode API integration
  - Dataclasses for OpenCodeAgent and OpenCodeModel with full type safety
  - Caching layer for agents and providers lists
  - Complete async/await pattern implementation
  - Integration with ProcessManager for lifecycle management
- **Dynamic Agent Role System**: Removed AgentRole enum restriction
  - spawn_agent now accepts any string role from OpenCode agent discovery
  - Enables runtime agent discovery and dynamic role assignment
  - Full backward compatibility maintained
- **Comprehensive Test Coverage**: 20 new Phase 3 tests (100% passing)
  - 10 tests for OpenCodeSessionManager Phase 3 features
  - 10 tests for new MCP tools (list_opencode_agents, list_opencode_models)
  - Integration tests with proper async mocking patterns
  - Complete coverage of error handling and edge cases

### Changed - Phase 3
- OpenCode service layer refactored to use centralized OpenCodeClient
- MCP server tool handlers updated with Phase 3 tool implementations
- spawn_agent role parameter type changed from enum to string for dynamic roles
- Session manager architecture enhanced with config management capabilities

### Fixed - Phase 3
- Test suite patching strategy corrected for opencode_service chain
- Parameter naming consistency (arguments vs args) in execute_command tests

### Documentation - Phase 3
- AKTIONSPLAN_PHASE3.md: Complete Phase 3 planning and implementation guide
- Archived resolved issues: io-block-spawn-agent.md, zombie-process-management.md
- Test documentation for all Phase 3 features

### Added - X^∞ Responsibility Tracking
- **BREAKING CHANGE**: Cap & Delegation Responsibility Fields for Agent Spawning
  - `original_task` field: Tracks the original task that started the work (task_id, title, description, requester, requested_at)
  - `cap_origin` field: Documents ultimate authority source (ultimate_authority, original_scope, granted_at, grant_context)
  - `delegation_context` field: Current delegator and delegated cap (delegator, delegator_cap, delegated_to, delegated_cap, constraints, phantom_level, delegated_at)
  - Full X^∞ compliance: Complete traceability of responsibility chains from original request through all delegation levels
  - All 3 fields are now **required** for `spawn_agent` MCP tool
  - SessionInfo model extended with Cap tracking fields
  - SpawnAgentRequest model extended with Cap tracking fields
  - SessionService automatically stores and propagates Cap fields through session lifecycle
  - MCP tool schema updated with detailed Cap field descriptions and examples
  - Helper functions for test data generation in test_session_models.py
  - 20 unit tests updated and passing for new Cap fields
  - Complete integration test coverage for Cap field propagation

### Added
- V2 Session-Based Architecture Migration completed
- Session Models: SpawnAgentRequest, SessionStatus, SessionInfo, AgentOutput
- SessionService with 6 core async methods for agent lifecycle management
- 7 new MCP tools with session-based interaction patterns
- Phase 4: Comprehensive integration test suite (15 end-to-end tests)
- Complete test coverage: 79 tests with 100% pass rate
- Backward compatibility layer with deprecation warnings for V1 tools
- SQLite WAL mode configuration for improved concurrency
- Enhanced Logfire integration for session tracking
- MockOpenCodeAPI framework for integration testing
- Performance benchmarks: <1s session creation, >5 msg/s throughput

### Changed
- Migrated from delegation-based to session-based architecture
- MCP server refactored to support both V1 (deprecated) and V2 tools
- OpenCode integration now uses session-based API patterns
- STATUS_REPORT.md updated to reflect V2 production-ready status

### Removed
- V1 delegation-based MCP tools (delegate_work, get_delegation_status, etc.)
- Deprecated tool handlers and warning blocks
- TestDeprecatedTools class from test suite
- DelegationService imports from server.py
- 268 lines of legacy V1 code

### Documentation
- Complete README.md rewrite for V2 session-based architecture

### Fixed
- **Asyncio Scoping Error in spawn_agent**: Removed redundant local `import asyncio` in SessionService.spawn_agent()
  - Root Cause: Local import in spawn_agent method (line 149) created scoping conflict
  - Error: "cannot access local variable 'asyncio' where it is not associated with a value"
  - Fix: Removed redundant import, using top-level asyncio import (line 12)
  - Impact: spawn_agent MCP tool now functional, no regressions in other tools
  - Test: Python import verification and SpawnAgentRequest model test passing

- **Test Import Errors**: Resolved all 'from src.' import paths in test files
  - Fixed test_integration_v2.py, test_session_service.py, test_process_manager.py
  - Corrected patch() calls to use correct module paths
  - All import errors eliminated (no more ModuleNotFoundError)
- **Scope Deviation Testing**: Added comprehensive test suite for ScopeDeviationDetector
  - 26 new tests covering all deviation types and scenarios
  - 100% test pass rate for scope_deviation.py
  - Coverage >95% for deviation detection logic

- Added V2 migration guide with tool mapping table
- Performance metrics section with test results
- Updated architecture diagram for session-based flow
- Comprehensive usage examples for all 9 MCP tools

## [v0.1.0] - Previous Version

### Added
- OpenCode API Client für dynamische Agent- und Model-Verwaltung
- Session Manager für OpenCode Server API Sessions
- Erweiterte OpenCode Service Integration
- Basis-Test-Suite (test_basic.py)
- Vollständige Dokumentation (architecture.md, design-decisions.md, api-analysis.md)
- Optionale Logfire-Konfiguration (Development-Mode ohne Token)

### Changed
- OpenCode Service nutzt nun API statt File System
- Logfire ist jetzt optional für Development
- Import-Fix für List-Typ in opencode_service.py

### Fixed
- Logfire-Authentifizierungsfehler in Development-Umgebung
- Missing List import in opencode_service.py
