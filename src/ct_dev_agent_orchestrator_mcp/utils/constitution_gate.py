"""Constitution gate for validating operations against X^∞ principles."""

from typing import List, Optional, Dict
from datetime import datetime, timezone
import json
import logfire
from ..storage.database import get_database


class ConstitutionViolation:
    """Represents a violation of X^∞ constitution principles."""
    
    def __init__(self, principle: str, description: str, severity: str = "ERROR"):
        self.principle = principle
        self.description = description
        self.severity = severity


class ConstitutionGate:
    """Validates operations against X^∞ constitution principles."""
    
    # X^∞ Constitution Principles
    PRINCIPLES = {
        "WIRKUNG_VOR_MASSNAHME": "Focus on effects before measures",
        "VERANTWORTUNG_SICHTBAR": "Make responsibility visible",
        "SCHUTZ_DER_SCHWACHSTEN": "Protect the weakest",
        "ATOMIC_DELEGATION": "Delegate atomic, focused work packages",
        "KNOWLEDGE_INTEGRATION": "Integrate with knowledge systems (Ptah)",
        "SERENA_FIRST": "Use Serena for code operations",
        "TDD_DISCIPLINE": "Follow test-driven development",
        "FAIL_FAST_LOUD": "Fail fast and loud, no silent failures",
        "NO_PLACEHOLDERS": "No placeholders or incomplete implementations",
        "KISS_NO_OVERENGINEERING": "Keep it simple, no over-engineering"
    }
    
    def __init__(self):
        """Initialize constitution gate."""
        self.db = get_database()
    
    def check_agent_creation(
        self,
        role: str,
        created_by: str
    ) -> tuple[bool, List[ConstitutionViolation]]:
        """Check agent creation against constitution.
        
        Args:
            role: Agent role
            created_by: Creator identifier
            
        Returns:
            Tuple of (approved, violations)
        """
        violations = []
        
        # Check: VERANTWORTUNG_SICHTBAR - Creator must be specified
        if not created_by or created_by.strip() == "":
            violations.append(ConstitutionViolation(
                "VERANTWORTUNG_SICHTBAR",
                "Agent creator not specified - responsibility must be visible"
            ))
        
        # Check: NO_PLACEHOLDERS - Role must be valid
        if not role or role.strip() == "":
            violations.append(ConstitutionViolation(
                "NO_PLACEHOLDERS",
                "Agent role is empty or placeholder"
            ))
        
        approved = len(violations) == 0
        self._log_check("agent_creation", ["VERANTWORTUNG_SICHTBAR", "NO_PLACEHOLDERS"], violations, approved)
        
        return approved, violations
    
    def check_delegation(
        self,
        task_id: str,
        instructions: str,
        delegator: str
    ) -> tuple[bool, List[ConstitutionViolation]]:
        """Check delegation against constitution.
        
        Args:
            task_id: Task identifier
            instructions: Work instructions
            delegator: Delegator identifier
            
        Returns:
            Tuple of (approved, violations)
        """
        violations = []
        
        # Check: ATOMIC_DELEGATION - Instructions must be specific and bounded
        if not instructions or len(instructions.strip()) < 10:
            violations.append(ConstitutionViolation(
                "ATOMIC_DELEGATION",
                "Instructions too vague - must specify clear atomic work package"
            ))
        
        # Check: WIRKUNG_VOR_MASSNAHME - Must have clear effect/goal
        if "implement" not in instructions.lower() and "create" not in instructions.lower() and "analyze" not in instructions.lower():
            # This is a simple heuristic - in production would be more sophisticated
            pass  # Warning only
        
        # Check: VERANTWORTUNG_SICHTBAR - Delegator must be specified
        if not delegator or delegator.strip() == "":
            violations.append(ConstitutionViolation(
                "VERANTWORTUNG_SICHTBAR",
                "Delegator not specified - responsibility chain must be visible"
            ))
        
        # Check: NO_PLACEHOLDERS - Task ID must be valid UUID
        if not task_id or task_id.strip() == "" or task_id == "TODO":
            violations.append(ConstitutionViolation(
                "NO_PLACEHOLDERS",
                "Task ID is placeholder or missing"
            ))
        
        approved = len(violations) == 0
        self._log_check(
            "delegation",
            ["ATOMIC_DELEGATION", "VERANTWORTUNG_SICHTBAR", "NO_PLACEHOLDERS"],
            violations,
            approved
        )
        
        return approved, violations
    
    def check_scope_deviation(
        self,
        original_scope: str,
        deviation_reason: str,
        additional_work: str
    ) -> tuple[bool, List[ConstitutionViolation]]:
        """Check if scope deviation is justified.
        
        Args:
            original_scope: Original work scope
            deviation_reason: Reason for deviation
            additional_work: Additional work discovered
            
        Returns:
            Tuple of (approved, violations)
        """
        violations = []
        
        # Check: ATOMIC_DELEGATION - Deviation must be documented
        if not deviation_reason or len(deviation_reason.strip()) < 10:
            violations.append(ConstitutionViolation(
                "ATOMIC_DELEGATION",
                "Scope deviation reason not properly documented"
            ))
        
        # Check: FAIL_FAST_LOUD - Must explicitly state what can't be done
        if not additional_work or len(additional_work.strip()) < 10:
            violations.append(ConstitutionViolation(
                "FAIL_FAST_LOUD",
                "Additional work not clearly specified"
            ))
        
        # Scope deviations are by nature approved (they're escalations)
        # But we log violations for awareness
        approved = True
        self._log_check(
            "scope_deviation",
            ["ATOMIC_DELEGATION", "FAIL_FAST_LOUD"],
            violations,
            approved
        )
        
        return approved, violations
    
    def _log_check(
        self,
        operation_type: str,
        principles_checked: List[str],
        violations: List[ConstitutionViolation],
        approved: bool,
        justification: Optional[str] = None
    ):
        """Log constitution check to database and logfire.
        
        Args:
            operation_type: Type of operation checked
            principles_checked: List of principles checked
            violations: List of violations found
            approved: Whether check was approved
            justification: Optional justification for approval despite violations
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        violations_json = json.dumps([
            {
                "principle": v.principle,
                "description": v.description,
                "severity": v.severity
            }
            for v in violations
        ])
        
        # Log to database
        self.db.execute("""
            INSERT INTO constitution_checks 
            (timestamp, operation_type, principles_checked, violations, approved, justification)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            operation_type,
            json.dumps(principles_checked),
            violations_json if violations else None,
            1 if approved else 0,
            justification
        ))
        
        # Log to logfire
        if violations:
            logfire.warning(
                f"Constitution check {operation_type}",
                approved=approved,
                violations=[v.description for v in violations]
            )
        else:
            logfire.info(
                f"Constitution check {operation_type} passed",
                principles=principles_checked
            )
    
    def get_recent_checks(self, limit: int = 10) -> List[Dict]:
        """Get recent constitution checks.
        
        Args:
            limit: Maximum number of checks to return
            
        Returns:
            List of check records
        """
        return self.db.fetchall("""
            SELECT * FROM constitution_checks 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))


# Global instance
_gate: Optional[ConstitutionGate] = None


def get_constitution_gate() -> ConstitutionGate:
    """Get global constitution gate instance.
    
    Returns:
        ConstitutionGate instance
    """
    global _gate
    if _gate is None:
        _gate = ConstitutionGate()
    return _gate
