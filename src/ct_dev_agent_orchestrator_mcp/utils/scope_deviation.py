"""
Scope Deviation Detection for Agent Sessions.

Provides utilities to detect when agent work deviates from expected scope,
following X^∞ principle: "Bei jeglicher Abweichung ist das Arbeitspaket 
zur Klärung an den Delegierenden zurückzugeben."
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import logfire


class ScopeDeviationDetector:
    """Detects scope deviations in agent sessions."""
    
    # Deviation severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    # Deviation types
    TYPE_SCOPE_DRIFT = "scope_drift"  # Work drifting beyond original scope
    TYPE_BLOCKING_ISSUE = "blocking_issue"  # Unexpected blocker encountered
    TYPE_ADDITIONAL_WORK = "additional_work"  # More work than expected
    TYPE_UNCLEAR_REQUIREMENTS = "unclear_requirements"  # Ambiguous instructions
    TYPE_DEPENDENCY_FAILURE = "dependency_failure"  # External dependency failed
    
    @staticmethod
    def detect_scope_keywords(message: str) -> Optional[Dict[str, Any]]:
        """Detect scope deviation keywords in agent messages.
        
        Args:
            message: Message text to analyze
            
        Returns:
            Deviation dict or None if no deviation detected
        """
        # Keywords indicating scope issues (case-insensitive)
        deviation_indicators = {
            ScopeDeviationDetector.TYPE_SCOPE_DRIFT: [
                "außerhalb des scopes",
                "beyond scope",
                "not in scope",
                "scope erweitern",
                "expand scope"
            ],
            ScopeDeviationDetector.TYPE_BLOCKING_ISSUE: [
                "blockiert",
                "blocked",
                "can't proceed",
                "cannot continue",
                "stuck"
            ],
            ScopeDeviationDetector.TYPE_ADDITIONAL_WORK: [
                "zusätzliche arbeit",
                "additional work",
                "more work needed",
                "requires more",
                "extra steps"
            ],
            ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS: [
                "unklar",
                "unclear",
                "ambiguous",
                "nicht verstanden",
                "don't understand",
                "need clarification"
            ],
            ScopeDeviationDetector.TYPE_DEPENDENCY_FAILURE: [
                "abhängigkeit fehlt",
                "dependency missing",
                "service unavailable",
                "external failure"
            ]
        }
        
        message_lower = message.lower()
        
        for deviation_type, keywords in deviation_indicators.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Calculate severity based on type and context
                    severity = ScopeDeviationDetector._calculate_severity(
                        deviation_type,
                        message_lower
                    )
                    
                    return {
                        "detected": True,
                        "type": deviation_type,
                        "severity": severity,
                        "message": f"Detected '{keyword}' in agent response",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "matched_keyword": keyword
                    }
        
        return None
    
    @staticmethod
    def _calculate_severity(deviation_type: str, message: str) -> str:
        """Calculate deviation severity based on type and context."""
        
        # Critical indicators
        if any(word in message for word in [
            "critical", "kritisch", "cannot continue", "komplett blockiert"
        ]):
            return ScopeDeviationDetector.SEVERITY_CRITICAL
        
        # High severity for blocking issues and dependency failures
        if deviation_type in [
            ScopeDeviationDetector.TYPE_BLOCKING_ISSUE,
            ScopeDeviationDetector.TYPE_DEPENDENCY_FAILURE
        ]:
            return ScopeDeviationDetector.SEVERITY_HIGH
        
        # Medium for unclear requirements and additional work
        if deviation_type in [
            ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS,
            ScopeDeviationDetector.TYPE_ADDITIONAL_WORK
        ]:
            return ScopeDeviationDetector.SEVERITY_MEDIUM
        
        # Default to low
        return ScopeDeviationDetector.SEVERITY_LOW
    
    @staticmethod
    def detect_from_messages(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect scope deviation from message history.
        
        Args:
            messages: List of message dicts with 'role' and 'parts'
            
        Returns:
            Deviation dict or None if no deviation detected
        """
        for msg in messages:
            if msg.get("role") == "assistant":
                # Check each text part
                for part in msg.get("parts", []):
                    if part.get("type") == "text":
                        text = part.get("text", "")
                        deviation = ScopeDeviationDetector.detect_scope_keywords(text)
                        if deviation:
                            logfire.warn(
                                "Scope deviation detected",
                                deviation_type=deviation["type"],
                                severity=deviation["severity"]
                            )
                            return deviation
        
        return None
    
    @staticmethod
    def should_escalate(deviation: Optional[Dict[str, Any]]) -> bool:
        """Determine if deviation should be escalated to delegator.
        
        Args:
            deviation: Deviation dict
            
        Returns:
            True if escalation needed
        """
        if not deviation:
            return False
        
        # Escalate critical and high severity
        if deviation.get("severity") in [
            ScopeDeviationDetector.SEVERITY_CRITICAL,
            ScopeDeviationDetector.SEVERITY_HIGH
        ]:
            return True
        
        # Escalate blocking issues regardless of severity
        if deviation.get("type") == ScopeDeviationDetector.TYPE_BLOCKING_ISSUE:
            return True
        
        return False
