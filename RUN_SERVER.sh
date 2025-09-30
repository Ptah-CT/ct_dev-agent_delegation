#!/bin/bash
# Agent Orchestrator MCP Server Startup Script

echo "🚀 Starting Agent Orchestrator MCP Server..."
echo ""

# Load secrets if available
if [ -f secrets.env ]; then
    echo "📝 Loading Logfire configuration from secrets.env..."
    export $(cat secrets.env | xargs)
else
    echo "⚠️  No secrets.env found - running without Logfire monitoring"
    echo "   (Create secrets.env with LOGFIRE_TOKEN for production monitoring)"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import mcp, logfire, httpx, psutil" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ All dependencies installed"
else
    echo "   ✗ Missing dependencies - run: pip3 install -e ."
    exit 1
fi

# Start server
echo ""
echo "▶️  Starting MCP Server..."
echo "   Logfire: https://logfire-us.pydantic.dev/ptah-ct/agent-orchestrator"
echo "   Press Ctrl+C to stop"
echo ""

python3 -m ct_dev_agent_orchestrator_mcp
