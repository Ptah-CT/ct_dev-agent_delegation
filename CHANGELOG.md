# Changelog

## [Unreleased]

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
