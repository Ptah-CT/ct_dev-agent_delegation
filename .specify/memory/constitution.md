<!--
═══════════════════════════════════════════════════════════════════════════════
SYNC IMPACT REPORT
═══════════════════════════════════════════════════════════════════════════════

VERSION CHANGE: 0.0.0 → 1.0.0
CHANGE TYPE: MAJOR - Initial Constitution Ratification
DATE: 2025-01-17

MODIFIED PRINCIPLES:
- NEW: All 10 core principles established from X^∞ framework
  1. Wirkung vor Maßnahme (Effect Before Action)
  2. Verantwortung sichtbar machen (Responsibility Transparency)
  3. Schutz der Schwächsten (Protection of the Weakest)
  4. Atomic Delegation (NON-NEGOTIABLE)
  5. Knowledge Management Integration (Ptah)
  6. Serena-First Code Operations
  7. Task Management Discipline
  8. Fail Fast and Loud
  9. No Placeholders/Mocks
  10. KISS & No Over-Engineering

ADDED SECTIONS:
- Development Process (3-phase workflow: PLANUNG, UMSETZUNG, ÜBERPRÜFUNG)
- System Constraints (host environment, code quality, documentation standards)
- Governance (amendment process, compliance review, related documents)

REMOVED SECTIONS:
- N/A (initial version)

TEMPLATES STATUS:
✅ .specify/templates/plan-template.md - ALIGNED
   - Constitution Check section present (line 47-50)
   - References constitution for gate evaluation
   - Workflow aligns with Phase 1: PLANUNG

✅ .specify/templates/tasks-template.md - ALIGNED
   - TDD enforcement matches Principle VIII (Fail Fast)
   - Sequential/parallel task marking supports atomic delegation
   - Phase structure matches constitution workflow

✅ .specify/templates/spec-template.md - ALIGNED
   - Focus on WHAT/WHY (not HOW) matches Principle I (Effect Before Action)
   - Clarity requirements match Principle II (Responsibility Transparency)
   - Review checklist supports quality gates

⚠ .github/prompts/*.md - REVIEW NEEDED
   - All prompt files should reference constitution principles
   - Agent-specific references (CLAUDE) need verification for generic applicability

FOLLOW-UP TODOS:
- [ ] Review .github/prompts/plan.prompt.md for constitution alignment
- [ ] Review .github/prompts/tasks.prompt.md for TDD enforcement
- [ ] Review .github/prompts/specify.prompt.md for effect-before-action principle
- [ ] Review .github/prompts/implement.prompt.md for atomic delegation enforcement
- [ ] Verify runtime guidance docs reference new constitution location
- [ ] Create migration guide if existing projects need constitution adoption

VALIDATION CHECKS:
✅ No remaining unexplained bracket tokens
✅ Version line matches report (1.0.0)
✅ Dates in ISO format (2025-01-17)
✅ Principles are declarative and testable
✅ All X^∞ principles integrated
✅ NASA Power of Ten rules incorporated
✅ CLAUDE.md principles embedded

COMMIT MESSAGE SUGGESTION:
docs: ratify constitution v1.0.0 (X^∞ Agent Orchestrator MCP governance)

Initial constitution establishing 10 core principles from X^∞ Quiet Revolution
framework, 3-phase development workflow, and strict quality gates. Integrates
Ptah knowledge management, Serena code operations, and NASA Power of Ten rules.

BREAKING CHANGES:
- All development MUST follow 3-phase workflow with Auctor approval gates
- All code operations MUST use Serena tools (no direct file manipulation)
- All work MUST be tracked in ct-task_mgmnt
- Zero tolerance for placeholders, mocks, or "partially working" code

═══════════════════════════════════════════════════════════════════════════════
-->

# Agent Orchestrator MCP Constitution

## Core Principles

### I. Wirkung vor Maßnahme (Effect Before Action)
Describe first *what should be achieved or prevented*, not what will be done. Every action, decision, or code change MUST begin with a clear statement of its intended effect. Implementation details follow only after the effect is understood and validated.

**Rationale**: Focusing on effects prevents solution-first thinking, ensures alignment with actual needs, and enables better evaluation of alternatives. This principle enforces outcome-oriented development.

### II. Verantwortung sichtbar machen (Responsibility Transparency)
Every statement, change, or decision explicitly carries its source of responsibility (Cap, Delegation, Authorship). No anonymous changes. All code, documentation, and decisions MUST identify who holds responsibility and under what authority (Cap-Potential, delegated authority, or authorship).

**Rationale**: Explicit responsibility creates accountability, enables traceability, and supports the X^∞ principle of responsibility conservation. It prevents diffusion of responsibility and ensures clear chains of authority.

### III. Schutz der Schwächsten (Protection of the Weakest)
Every decision is measured by its impact on those who need protection (users, junior developers, systems under load, edge cases). Design decisions MUST explicitly consider and document their effect on the most vulnerable parts of the system.

**Rationale**: Following X^∞ protection bias principle (w_E' = reciprocal weighting), system stability emerges from protecting the weakest elements. This prevents cascading failures and ensures robust systems.

### IV. Atomic Delegation (NON-NEGOTIABLE)
Work packages are delegated atomically with specific instructions on what to achieve. Any deviation (extra work, problems, additional steps) MUST return the package to the delegator for clarification. No autonomous scope expansion.

**Rationale**: Atomic delegation prevents scope creep, maintains control flow, and ensures that Cap-Potential is properly distributed. Deviation without consultation violates responsibility conservation.

### V. Knowledge Management Integration
Ptah (Knowledge Manager) is the extended memory for all development work. Every conversation, insight, and decision MUST be shared with Ptah BEFORE starting work and AFTER each significant step. All research originates from Ptah.

**Rationale**: Centralized knowledge prevents information loss, enables learning across contexts, and ensures consistency. Ptah serves as the system's collective memory and prevents redundant discovery.

### VI. Serena-First Code Operations
ALL file operations (search, read, write, modify) MUST use Serena tools. Direct file manipulation is prohibited. Serena tools provide semantic understanding and resource efficiency.

**Rationale**: Semantic tools enable intelligent code navigation, reduce unnecessary reading, and enforce structured code understanding. Resource efficiency is maintained through targeted operations rather than brute-force file scanning.

### VII. Task Management Discipline
All activities MUST be documented and organized in ct-task_mgmnt. Before starting work, verify corresponding task exists or create one. Work without task tracking is prohibited.

**Rationale**: Task tracking ensures traceability, enables project oversight, and maintains connection between work and requirements. Prevents orphaned work and enables proper project management.

### VIII. Fail Fast and Loud
Systems are digital: 0 or 1, not "partially working". There is no "core fix works but has issues" - that is failure. There is no "that's a different problem" when you encounter issues - if you step in it, you own it. No one else will carry the burden.

**Rationale**: Binary thinking prevents technical debt accumulation. Partial solutions create maintenance nightmares. Strict failure handling prevents problem diffusion and ensures clean system states.

### IX. No Placeholders, No Mocks, Only Functional Code
Placeholders and mocks are prohibited. Only production-ready, functional code. Code that doesn't work is not code - it's technical debt.

**Rationale**: Placeholders accumulate and become permanent. Mocks hide integration issues. Functional-only code ensures that what exists actually works, reducing debugging and maintenance burden.

### X. KISS & No Over-Engineering
Of all options, choose the simplest - without impacting existing or desired functionality. No backward compatibility requirements. Simple solutions only.

**Rationale**: Simplicity reduces cognitive load, maintenance burden, and bug surface area. Over-engineering creates complexity debt. YAGNI (You Aren't Gonna Need It) principles prevent premature optimization.

## Development Process (NON-NEGOTIABLE)

### Phase 1: PLANUNG (Team mode: PLAN)
**CODE CHANGES STRICTLY FORBIDDEN**

1. Understand requirement/issue
2. Create documentation as .md
3. Inform Knowledge Management, receive context
4. Delegation: Analyze current state via agents (for issues: root cause analysis by multiple experts simultaneously)
5. Delegation: Deep Research via Knowledge Management (frameworks, specs, code examples, best practices, RTFM)
6. Delegation: Define target state through architects + experts
7. Delegation: Peer review by Philosophical Reviewer
8. Delegation: Create implementation plan with milestones and work packages by Planner
9. Document in .md
10. Task Management in ct_dev-task_mgmnt: Create tasks
11. **FREIGABE DURCH AUCTOR (Release by Auctor required)**

### Phase 2: UMSETZUNG (Team mode: EDIT)
1. Delegation: Create branch and switch to it
2. After 2.1: Delegation: Implement work packages, remove deprecated code
3. After 2.1: Delegation: Immediate review after implementation by Review Agents and Philosophical Reviewer
4. After 2.2 & 2.3: Delegation: Syntax review for production-ready, error-free, maintainable code

### Phase 3: ÜBERPRÜFUNG (Team mode: ORGANIZE)
1. After 2.4: Delegation: Build and restart
2. After 3.1: Realistic tests from user perspective
3. After 3.2: Delegation: Complete review by Review Agent and Philosophical Reviewer
4. **FREIGABE DURCH AUCTOR (Release by Auctor required)**
5. Inform Knowledge Management
6. Close tasks
7. Update documentation project-wide
8. Delegation: Post-work: Move/delete test/debug/deprecated files
9. Maintain changelog and gitignore
10. Commit, Push, PR creation
11. Final report

## System Constraints

### Host Environment
- Python native, NO VENV, no uv (unless absolutely necessary for 3rd party vendors)
- NO Docker
- Python manually installed, libraries installed with sudo
- Firewall disabled, IP6 disabled (MUST remain disabled)
- Network separated from web via NAT
- System MUST be kept clean
- Development: /home/auctor/dev
- Services: /home/auctor/srv
- Tests: in respective tests/ directories
- Debug: in debug/ directories
- Temporary test/debug files MUST be deleted immediately
- Logging with logfire (not local, except rare debug exceptions)

### Code Quality (NASA Power of Ten Compliance)
1. Simple control flow - no goto, setjmp/longjmp, no recursion
2. All loops MUST have fixed upper bounds
3. No dynamic memory allocation after initialization
4. Functions limited to 60 lines
5. Minimum 2 assertions per function
6. Narrowest possible data scope
7. All non-void function return values MUST be checked
8. Limited preprocessor use, no conditional compilation
9. Pointer restrictions: max 1 dereferencing level, no function pointers
10. Zero warnings policy: all compiler warnings enabled, all must pass

### Documentation Standards
- Systemic documents: German (precise, philosophical)
- Technical implementations: English (pragmatic, functional)
- Project languages: German & English
- All documents follow 🜄 structure: Ziel, Kontext, Verantwortung, Prüfung, Risiken, Aufgaben
- Checklists always use `- [ ]` format
- Symbol 🜄 = systemic responsibility reference
- No emojis except 🜄, strictly functional design

## Governance

### Constitution Authority
This constitution supersedes all other practices and guidelines. It embodies X^∞ principles of responsibility conservation, protection bias, and postmoral evaluation (effect-based, not intention-based).

### Amendment Process
1. Amendments MUST document version change (semantic versioning: MAJOR.MINOR.PATCH)
2. MAJOR: Backward incompatible governance/principle removals or redefinitions
3. MINOR: New principle/section added or materially expanded guidance
4. PATCH: Clarifications, wording, typo fixes, non-semantic refinements
5. All amendments require Sync Impact Report
6. Dependent templates MUST be updated for consistency
7. Final approval: **Auctor Freigabe**

### Compliance Review
- All PRs/reviews MUST verify compliance with these principles
- Complexity MUST be justified against KISS principle
- Violations require documentation of Cap-Potential and responsibility chain
- Opportunitäts-Ethik: Check if decision blocks/delays other necessary decisions
- Runtime development guidance via CLAUDE.md and mitgeltende Dokumente

### Related Documents
Primary guidance: /home/auctor/CLAUDE.md
Supporting documents:
- /home/auctor/XInfty-AI-Debian-Host-System-Rules.md
- /home/auctor/X^∞-Seed.txt
- /home/auctor/XInfty_dev-Design_Guide/SYSTEMIC_STYLE_GUIDE.md
- /home/auctor/10_coding_rules.md

**Version**: 1.0.0 | **Ratified**: 2025-01-17 | **Last Amended**: 2025-01-17