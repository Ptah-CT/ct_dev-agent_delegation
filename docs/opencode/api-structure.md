# OpenCode Server API Structure

Basierend auf https://opencode.ai/docs/server/

## Kern-Endpunkte

### App Management
- `GET /app` - Get app info
- `POST /app/init` - Initialize the app

### Config
- `GET /config` - Get config info  
- `GET /config/providers` - List providers and default models

### Sessions
- Siehe vollständige Dokumentation in server-api-endpoints.html

## Wichtige Erkenntnisse
1. Alle Funktionen über HTTP/REST API verfügbar
2. Agents, Models, Tools dynamisch abrufbar
3. Session Management integriert
4. Provider-agnostic (verschiedene AI-Modelle)
