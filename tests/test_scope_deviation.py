"""Tests for Scope Deviation Detection in OpenCode API integration.

Tests cover:
- ScopeDeviationDetector unit tests
- Integration with session_service
- Detection of various deviation types
- Severity calculation
- Escalation logic

Author: OpenCode Phase 1 Fix & Deviation Detection
Coverage Target: >80% for scope_deviation.py
"""

import pytest
from datetime import datetime
from ct_dev_agent_delegation_mcp.utils.scope_deviation import ScopeDeviationDetector


class TestScopeDeviationDetector:
    """Unit tests for ScopeDeviationDetector."""
    
    def test_detect_scope_drift(self):
        """Test detection of scope drift keywords."""
        message = "This work is beyond scope of the original task"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["detected"] is True
        assert deviation["type"] == ScopeDeviationDetector.TYPE_SCOPE_DRIFT
        assert "beyond scope" in deviation["matched_keyword"]
    
    def test_detect_blocking_issue(self):
        """Test detection of blocking issues."""
        message = "I am blocked waiting for external API"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["detected"] is True
        assert deviation["type"] == ScopeDeviationDetector.TYPE_BLOCKING_ISSUE
        assert deviation["severity"] == ScopeDeviationDetector.SEVERITY_HIGH
        assert "blocked" in deviation["matched_keyword"]
    
    def test_detect_unclear_requirements(self):
        """Test detection of unclear requirements."""
        message = "The requirements are unclear, need clarification"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["detected"] is True
        assert deviation["type"] == ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS
        assert deviation["severity"] == ScopeDeviationDetector.SEVERITY_MEDIUM
    
    def test_detect_additional_work(self):
        """Test detection of additional work needed."""
        message = "This requires more work than expected"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["detected"] is True
        assert deviation["type"] == ScopeDeviationDetector.TYPE_ADDITIONAL_WORK
    
    def test_detect_dependency_failure(self):
        """Test detection of dependency failures."""
        message = "External service unavailable, cannot proceed"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["detected"] is True
        assert deviation["type"] == ScopeDeviationDetector.TYPE_DEPENDENCY_FAILURE
        assert deviation["severity"] == ScopeDeviationDetector.SEVERITY_HIGH
    
    def test_no_deviation_in_normal_message(self):
        """Test that normal messages don't trigger deviation detection."""
        message = "Implementation is progressing well, all tests passing"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is None
    
    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        message = "I am BLOCKED by the database issue"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["type"] == ScopeDeviationDetector.TYPE_BLOCKING_ISSUE
    
    def test_german_keywords(self):
        """Test detection of German deviation keywords."""
        message = "Die Anforderungen sind unklar"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["type"] == ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS


class TestSeverityCalculation:
    """Tests for severity calculation logic."""
    
    def test_critical_severity_keyword(self):
        """Test critical severity based on keywords."""
        message = "This is a critical blocker, cannot continue"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert deviation["severity"] == ScopeDeviationDetector.SEVERITY_CRITICAL
    
    def test_high_severity_for_blocking(self):
        """Test high severity for blocking issues."""
        deviation_type = ScopeDeviationDetector.TYPE_BLOCKING_ISSUE
        message = "blocked"
        severity = ScopeDeviationDetector._calculate_severity(deviation_type, message)
        
        assert severity == ScopeDeviationDetector.SEVERITY_HIGH
    
    def test_medium_severity_for_unclear(self):
        """Test medium severity for unclear requirements."""
        deviation_type = ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS
        message = "unclear requirements"
        severity = ScopeDeviationDetector._calculate_severity(deviation_type, message)
        
        assert severity == ScopeDeviationDetector.SEVERITY_MEDIUM
    
    def test_low_severity_default(self):
        """Test low severity as default."""
        deviation_type = ScopeDeviationDetector.TYPE_SCOPE_DRIFT
        message = "drifting slightly"
        severity = ScopeDeviationDetector._calculate_severity(deviation_type, message)
        
        assert severity == ScopeDeviationDetector.SEVERITY_LOW


class TestEscalationLogic:
    """Tests for escalation decision logic."""
    
    def test_escalate_critical_severity(self):
        """Test escalation for critical severity."""
        deviation = {
            "detected": True,
            "type": ScopeDeviationDetector.TYPE_SCOPE_DRIFT,
            "severity": ScopeDeviationDetector.SEVERITY_CRITICAL,
            "message": "Critical issue"
        }
        
        assert ScopeDeviationDetector.should_escalate(deviation) is True
    
    def test_escalate_high_severity(self):
        """Test escalation for high severity."""
        deviation = {
            "detected": True,
            "type": ScopeDeviationDetector.TYPE_SCOPE_DRIFT,
            "severity": ScopeDeviationDetector.SEVERITY_HIGH,
            "message": "High severity issue"
        }
        
        assert ScopeDeviationDetector.should_escalate(deviation) is True
    
    def test_escalate_blocking_regardless_severity(self):
        """Test escalation for blocking issues regardless of severity."""
        deviation = {
            "detected": True,
            "type": ScopeDeviationDetector.TYPE_BLOCKING_ISSUE,
            "severity": ScopeDeviationDetector.SEVERITY_LOW,
            "message": "Blocking"
        }
        
        assert ScopeDeviationDetector.should_escalate(deviation) is True
    
    def test_no_escalate_medium_severity(self):
        """Test no escalation for medium severity non-blocking."""
        deviation = {
            "detected": True,
            "type": ScopeDeviationDetector.TYPE_UNCLEAR_REQUIREMENTS,
            "severity": ScopeDeviationDetector.SEVERITY_MEDIUM,
            "message": "Medium severity"
        }
        
        assert ScopeDeviationDetector.should_escalate(deviation) is False
    
    def test_no_escalate_low_severity(self):
        """Test no escalation for low severity."""
        deviation = {
            "detected": True,
            "type": ScopeDeviationDetector.TYPE_SCOPE_DRIFT,
            "severity": ScopeDeviationDetector.SEVERITY_LOW,
            "message": "Low severity"
        }
        
        assert ScopeDeviationDetector.should_escalate(deviation) is False
    
    def test_no_escalate_none_deviation(self):
        """Test no escalation when deviation is None."""
        assert ScopeDeviationDetector.should_escalate(None) is False


class TestDetectFromMessages:
    """Tests for detect_from_messages with message history."""
    
    def test_detect_from_assistant_message(self):
        """Test detection from assistant message in history."""
        messages = [
            {
                "role": "user",
                "parts": [{"type": "text", "text": "Please implement feature X"}]
            },
            {
                "role": "assistant",
                "parts": [{"type": "text", "text": "I am blocked by missing API documentation"}]
            }
        ]
        
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        assert deviation is not None
        assert deviation["type"] == ScopeDeviationDetector.TYPE_BLOCKING_ISSUE
    
    def test_ignore_user_messages(self):
        """Test that user messages are not checked for deviations."""
        messages = [
            {
                "role": "user",
                "parts": [{"type": "text", "text": "I am blocked"}]
            }
        ]
        
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        assert deviation is None
    
    def test_no_detection_in_clean_messages(self):
        """Test no detection in clean message history."""
        messages = [
            {
                "role": "assistant",
                "parts": [{"type": "text", "text": "Implementation completed successfully"}]
            }
        ]
        
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        assert deviation is None
    
    def test_multiple_text_parts(self):
        """Test detection across multiple text parts."""
        messages = [
            {
                "role": "assistant",
                "parts": [
                    {"type": "text", "text": "First part is fine"},
                    {"type": "text", "text": "But this part mentions we are blocked"}
                ]
            }
        ]
        
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        assert deviation is not None
    
    def test_empty_message_list(self):
        """Test with empty message list."""
        messages = []
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        assert deviation is None
    
    def test_first_deviation_wins(self):
        """Test that first deviation found is returned."""
        messages = [
            {
                "role": "assistant",
                "parts": [{"type": "text", "text": "I am blocked here"}]
            },
            {
                "role": "assistant",
                "parts": [{"type": "text", "text": "And unclear requirements there"}]
            }
        ]
        
        deviation = ScopeDeviationDetector.detect_from_messages(messages)
        
        # Should return first deviation (BLOCKING_ISSUE)
        assert deviation is not None
        assert deviation["type"] == ScopeDeviationDetector.TYPE_BLOCKING_ISSUE


class TestTimestampGeneration:
    """Tests for timestamp generation in deviations."""
    
    def test_deviation_has_timestamp(self):
        """Test that detected deviations include timestamp."""
        message = "I am blocked"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        assert "timestamp" in deviation
        assert deviation["timestamp"].endswith("Z")  # ISO 8601 with Z suffix
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO 8601 format."""
        message = "blocked"
        deviation = ScopeDeviationDetector.detect_scope_keywords(message)
        
        assert deviation is not None
        # Should be parseable as ISO 8601
        timestamp_str = deviation["timestamp"].rstrip("Z")
        try:
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail("Timestamp is not valid ISO 8601 format")


# Coverage summary for scope_deviation.py
"""
Expected coverage:
- detect_scope_keywords: 100%
- _calculate_severity: 100%
- detect_from_messages: 100%
- should_escalate: 100%
- All deviation types: covered
- All severity levels: covered
- Edge cases: covered

Total: >95% coverage
"""
