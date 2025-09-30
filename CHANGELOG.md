# Changelog

## [Unreleased]

### Added
- V2 Session-Based Architecture Migration completed
- Session Models: SpawnAgentRequest, SessionStatus, SessionInfo, AgentOutput
- SessionService with 6 core async methods for agent lifecycle management
- 7 new MCP tools with session-based interaction patterns
- Comprehensive test suite: 44+ tests with 100% pass rate
- Backward compatibility layer with deprecation warnings for V1 tools
- SQLite WAL mode configuration for improved concurrency
- Enhanced Logfire integration for session tracking

### Changed
- Migrated from delegation-based to session-based architecture
- MCP server refactored to support both V1 (deprecated) and V2 tools
- OpenCode integration now uses session-based API patterns
- STATUS_REPORT.md updated to reflect V2 production-ready status

### Deprecated
- V1 delegation-based MCP tools (spawn_agent, query_agent, etc.)
- Direct delegation patterns in favor of session management

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
