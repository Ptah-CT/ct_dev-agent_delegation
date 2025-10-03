"""
Centralized configuration management for Agent Orchestrator.
"""
import os
import logfire


def configure_logfire() -> None:
    """
    Configure Logfire with token from environment or disable if no token.
    
    This function centralizes Logfire configuration logic that was previously
    duplicated across multiple service files.
    """
    try:
        token = os.getenv("LOGFIRE_TOKEN")
        if token:
            logfire.configure(token=token)
        else:
            logfire.configure(send_to_logfire=False)
    except Exception:
        logfire.configure(send_to_logfire=False)


def get_logfire_config() -> dict:
    """
    Get current Logfire configuration status.
    
    Returns:
        dict: Configuration status with token presence and enabled state
    """
    token = os.getenv("LOGFIRE_TOKEN")
    return {
        "token_present": bool(token),
        "enabled": bool(token),
        "send_to_logfire": bool(token)
    }
