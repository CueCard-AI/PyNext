"""
PyNext Linting - Custom Rules

10 PyNext-specific linting rules to catch common mistakes.
These complement ruff's standard Python rules.

Rules:
    PNX001: Unused Signal - signal created but never read
    PNX002: Signal in loop - creating signals inside loops
    PNX003: Missing component return - function doesn't return element
    PNX004: Invalid prop type - prop not JSON-serializable for island
    PNX005: Server import in island - importing server-only code
    PNX006: Invalid route name - route file doesn't match convention
    PNX007: Missing page export - page.py missing page() function
    PNX008: Untracked effect - Effect without dependency tracking
    PNX009: Direct signal mutation - using .value instead of .set()
    PNX010: Missing metadata - page without Metadata export

Usage:
    from pynext.lint.rules import run_rules, get_all_rules
    
    errors = run_rules(source_code, filename)
    for error in errors:
        print(f"{error.rule}: {error.message}")
"""

from pynext.lint.rules.signals import SignalLinter
from pynext.lint.rules.components import ComponentLinter
from pynext.lint.rules.islands import IslandLinter
from pynext.lint.rules.routes import RouteLinter

from pynext.lint.rules.base import LintError, LintResult, BaseLinter


# =============================================================================
# Rule Registry
# =============================================================================

RULE_REGISTRY = {
    # Signal rules
    "PNX001": {
        "name": "unused-signal",
        "description": "Signal is created but never read",
        "linter": SignalLinter,
        "auto_fix": True,
        "severity": "warning",
    },
    "PNX002": {
        "name": "signal-in-loop",
        "description": "Signal created inside a loop",
        "linter": SignalLinter,
        "auto_fix": False,
        "severity": "error",
    },
    
    # Component rules
    "PNX003": {
        "name": "missing-return",
        "description": "Component function doesn't return an element",
        "linter": ComponentLinter,
        "auto_fix": True,
        "severity": "error",
    },
    "PNX004": {
        "name": "invalid-prop-type",
        "description": "Island prop is not JSON-serializable",
        "linter": IslandLinter,
        "auto_fix": False,
        "severity": "error",
    },
    "PNX005": {
        "name": "server-import-in-island",
        "description": "Island imports server-only code",
        "linter": IslandLinter,
        "auto_fix": False,
        "severity": "error",
    },
    
    # Route rules
    "PNX006": {
        "name": "invalid-route-name",
        "description": "Route file name doesn't match convention",
        "linter": RouteLinter,
        "auto_fix": True,
        "severity": "warning",
    },
    "PNX007": {
        "name": "missing-page-export",
        "description": "page.py is missing the page() function",
        "linter": RouteLinter,
        "auto_fix": True,
        "severity": "error",
    },
    
    # Effect rules
    "PNX008": {
        "name": "untracked-effect",
        "description": "Effect doesn't track any dependencies",
        "linter": SignalLinter,
        "auto_fix": False,
        "severity": "warning",
    },
    
    # Signal mutation rules
    "PNX009": {
        "name": "direct-signal-mutation",
        "description": "Signal mutated directly instead of using .set()",
        "linter": SignalLinter,
        "auto_fix": True,
        "severity": "error",
    },
    
    # Metadata rules
    "PNX010": {
        "name": "missing-metadata",
        "description": "Page is missing Metadata export",
        "linter": RouteLinter,
        "auto_fix": True,
        "severity": "info",
    },
}


def get_all_rules() -> dict:
    """
    Get all PyNext linting rules.
    
    Returns:
        Dictionary of rule_id -> rule_info
    """
    return RULE_REGISTRY.copy()


def get_rule(rule_id: str) -> dict:
    """
    Get information about a specific rule.
    
    Args:
        rule_id: The rule identifier (e.g., "PNX001")
        
    Returns:
        Rule information dictionary
        
    Raises:
        KeyError: If rule doesn't exist
    """
    if rule_id not in RULE_REGISTRY:
        raise KeyError(f"Unknown rule: {rule_id}")
    return RULE_REGISTRY[rule_id]


def explain_rule(rule_id: str) -> str:
    """
    Get a detailed explanation of a rule.
    
    Args:
        rule_id: The rule identifier
        
    Returns:
        Human-readable explanation
    """
    if rule_id not in RULE_REGISTRY:
        return f"Unknown rule: {rule_id}"
    
    rule = RULE_REGISTRY[rule_id]
    linter_class = rule["linter"]
    
    # Get explanation from linter if available
    if hasattr(linter_class, "explain"):
        return linter_class.explain(rule_id)
    
    return f"""
Rule: {rule_id}
Name: {rule['name']}
Severity: {rule['severity']}
Auto-fix: {'Yes' if rule['auto_fix'] else 'No'}

Description:
{rule['description']}
"""


# =============================================================================
# Rule Execution
# =============================================================================

def run_rules(
    source: str,
    filename: str = "<unknown>",
    enabled_rules: set = None,
) -> list[LintError]:
    """
    Run all enabled rules on source code.
    
    Args:
        source: Python source code to check
        filename: Name of the file (for error messages)
        enabled_rules: Set of rule IDs to run (all if None)
        
    Returns:
        List of LintError objects
    """
    errors = []
    
    if enabled_rules is None:
        enabled_rules = set(RULE_REGISTRY.keys())
    
    # Group rules by linter
    linters_to_run = set()
    for rule_id in enabled_rules:
        if rule_id in RULE_REGISTRY:
            linters_to_run.add(RULE_REGISTRY[rule_id]["linter"])
    
    # Run each linter once
    for linter_class in linters_to_run:
        try:
            linter = linter_class()
            linter_errors = linter.check(source, filename, enabled_rules)
            errors.extend(linter_errors)
        except Exception as e:
            # Don't crash on linter errors
            errors.append(LintError(
                rule="PNX000",
                message=f"Linter error: {e}",
                line=0,
                column=0,
                severity="error",
            ))
    
    return sorted(errors, key=lambda e: (e.line, e.column))


def run_rules_on_file(
    file_path: str,
    enabled_rules: set = None,
) -> list[LintError]:
    """
    Run rules on a file.
    
    Args:
        file_path: Path to Python file
        enabled_rules: Set of rule IDs to run
        
    Returns:
        List of LintError objects
    """
    from pathlib import Path
    
    path = Path(file_path)
    if not path.exists():
        return [LintError(
            rule="PNX000",
            message=f"File not found: {file_path}",
            line=0,
            column=0,
            severity="error",
        )]
    
    source = path.read_text()
    return run_rules(source, str(path), enabled_rules)


__all__ = [
    # Registry
    "RULE_REGISTRY",
    "get_all_rules",
    "get_rule",
    "explain_rule",
    
    # Execution
    "run_rules",
    "run_rules_on_file",
    
    # Linters
    "SignalLinter",
    "ComponentLinter",
    "IslandLinter",
    "RouteLinter",
    
    # Types
    "LintError",
    "LintResult",
    "BaseLinter",
]

