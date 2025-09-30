# Changelog

## [Unreleased]

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
