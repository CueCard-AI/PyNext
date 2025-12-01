"""
PyNext Query Analyzer Module.

Provides automatic query analysis, slow query detection, EXPLAIN capture,
index suggestions, and query optimization hints.

Why Query Analysis?
──────────────────
Slow queries can cripple your application. This module helps you:
1. Detect slow queries before users complain
2. Understand WHY queries are slow (via EXPLAIN)
3. Get actionable suggestions (missing indexes, query rewrites)
4. Track patterns and trends over time

Analysis Flow:
    Query Executed → Timing Check → Slow? → EXPLAIN → Parse → Suggestions

Usage Levels:

Level 1: Basic Detection (Zero Config)
    adapter = PostgresAdapter("postgresql://...", analyzer=True)
    # Automatically logs slow queries

Level 2: Custom Threshold
    adapter = PostgresAdapter("postgresql://...", analyzer=AnalyzerConfig(
        slow_threshold_ms=50,
    ))

Level 3: Full Analysis
    adapter = PostgresAdapter("postgresql://...", analyzer=AnalyzerConfig(
        slow_threshold_ms=50,
        auto_explain=True,
        suggest_indexes=True,
        suggest_rewrites=True,
    ))

Manual Analysis:
    result = await adapter.analyze_query("SELECT * FROM users WHERE email = $1")
    print(result.suggestions)  # ["Add index on users.email"]

AI-Friendly Design:
- Clear suggestion messages
- Structured output format
- Pattern-based detection
- Easy to extend
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AnalyzerConfig:
    """Configuration for query analyzer.
    
    Attributes:
        enabled: Whether analysis is enabled
        slow_threshold_ms: Queries slower than this are analyzed
        auto_explain: Automatically run EXPLAIN on slow queries
        suggest_indexes: Generate index suggestions
        suggest_rewrites: Generate query rewrite suggestions
        max_explain_cost: Max cost before suggesting optimization
        store_history: Store query history for pattern detection
        history_size: Maximum number of queries to store
        
    Example:
        # Default configuration (just detection)
        config = AnalyzerConfig()
        
        # Full analysis with suggestions
        config = AnalyzerConfig(
            slow_threshold_ms=50,
            auto_explain=True,
            suggest_indexes=True,
            suggest_rewrites=True,
        )
    """
    enabled: bool = True
    slow_threshold_ms: float = 100.0
    auto_explain: bool = True
    suggest_indexes: bool = True
    suggest_rewrites: bool = True
    max_explain_cost: float = 1000.0
    store_history: bool = True
    history_size: int = 1000
    
    # Callbacks
    on_slow_query: Optional[Callable[["AnalysisResult"], None]] = None
    on_suggestion: Optional[Callable[["QuerySuggestion"], None]] = None


# ============================================================================
# Enums
# ============================================================================

class SuggestionType(str, Enum):
    """Types of query suggestions."""
    INDEX = "index"           # Missing index suggestion
    REWRITE = "rewrite"       # Query rewrite suggestion
    LIMIT = "limit"           # Missing LIMIT clause
    SELECT_STAR = "select_star"  # SELECT * warning
    N_PLUS_ONE = "n_plus_one"    # N+1 query pattern
    SORT = "sort"             # Unnecessary or expensive sort
    JOIN = "join"             # Join optimization
    FILTER = "filter"         # Filter optimization


class ScanType(str, Enum):
    """Types of scans in EXPLAIN output."""
    SEQ_SCAN = "Seq Scan"
    INDEX_SCAN = "Index Scan"
    INDEX_ONLY_SCAN = "Index Only Scan"
    BITMAP_SCAN = "Bitmap Heap Scan"
    NESTED_LOOP = "Nested Loop"
    HASH_JOIN = "Hash Join"
    MERGE_JOIN = "Merge Join"
    SORT = "Sort"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ExplainNode:
    """A node in the EXPLAIN output tree.
    
    Represents one operation in the query execution plan.
    
    Attributes:
        node_type: Type of operation (Seq Scan, Index Scan, etc.)
        relation: Table name if applicable
        alias: Table alias if applicable
        startup_cost: Cost before first row
        total_cost: Total estimated cost
        rows: Estimated rows
        width: Estimated row width
        actual_time: Actual execution time (if ANALYZE)
        actual_rows: Actual rows returned (if ANALYZE)
        filter: Filter condition
        index_name: Index used (if index scan)
        index_cond: Index condition
        children: Child nodes
    """
    node_type: str
    relation: Optional[str] = None
    alias: Optional[str] = None
    startup_cost: float = 0.0
    total_cost: float = 0.0
    rows: int = 0
    width: int = 0
    actual_time: Optional[float] = None
    actual_rows: Optional[int] = None
    filter: Optional[str] = None
    index_name: Optional[str] = None
    index_cond: Optional[str] = None
    children: List["ExplainNode"] = field(default_factory=list)
    
    @property
    def is_seq_scan(self) -> bool:
        """Check if this is a sequential scan."""
        return self.node_type == ScanType.SEQ_SCAN.value
    
    @property
    def is_index_scan(self) -> bool:
        """Check if this is an index scan."""
        return self.node_type in (
            ScanType.INDEX_SCAN.value,
            ScanType.INDEX_ONLY_SCAN.value,
        )


@dataclass
class ExplainResult:
    """Parsed EXPLAIN output.
    
    Contains the full execution plan as a tree of nodes.
    
    Attributes:
        plan: Root node of the execution plan
        planning_time: Time spent planning (ms)
        execution_time: Time spent executing (ms)
        total_cost: Total estimated cost
        raw_output: Original EXPLAIN output
    """
    plan: Optional[ExplainNode] = None
    planning_time: Optional[float] = None
    execution_time: Optional[float] = None
    total_cost: float = 0.0
    raw_output: str = ""
    
    @classmethod
    def from_json(cls, explain_json: Dict[str, Any]) -> "ExplainResult":
        """Parse EXPLAIN JSON output.
        
        Args:
            explain_json: Output from EXPLAIN (FORMAT JSON)
        
        Returns:
            Parsed ExplainResult
        """
        result = cls(raw_output=str(explain_json))
        
        if not explain_json:
            return result
        
        # EXPLAIN JSON returns a list with one element
        if isinstance(explain_json, list) and explain_json:
            explain_json = explain_json[0]
        
        # Parse plan
        if "Plan" in explain_json:
            result.plan = cls._parse_plan_node(explain_json["Plan"])
            result.total_cost = result.plan.total_cost if result.plan else 0.0
        
        # Parse timing
        result.planning_time = explain_json.get("Planning Time")
        result.execution_time = explain_json.get("Execution Time")
        
        return result
    
    @classmethod
    def _parse_plan_node(cls, node_dict: Dict[str, Any]) -> ExplainNode:
        """Parse a single plan node."""
        node = ExplainNode(
            node_type=node_dict.get("Node Type", "Unknown"),
            relation=node_dict.get("Relation Name"),
            alias=node_dict.get("Alias"),
            startup_cost=node_dict.get("Startup Cost", 0.0),
            total_cost=node_dict.get("Total Cost", 0.0),
            rows=node_dict.get("Plan Rows", 0),
            width=node_dict.get("Plan Width", 0),
            actual_time=node_dict.get("Actual Total Time"),
            actual_rows=node_dict.get("Actual Rows"),
            filter=node_dict.get("Filter"),
            index_name=node_dict.get("Index Name"),
            index_cond=node_dict.get("Index Cond"),
        )
        
        # Parse children
        if "Plans" in node_dict:
            for child_dict in node_dict["Plans"]:
                node.children.append(cls._parse_plan_node(child_dict))
        
        return node
    
    def find_seq_scans(self) -> List[ExplainNode]:
        """Find all sequential scans in the plan."""
        if not self.plan:
            return []
        
        seq_scans = []
        
        def walk(node: ExplainNode):
            if node.is_seq_scan and node.relation:
                seq_scans.append(node)
            for child in node.children:
                walk(child)
        
        walk(self.plan)
        return seq_scans
    
    def find_expensive_sorts(self, threshold: float = 100.0) -> List[ExplainNode]:
        """Find expensive sort operations."""
        if not self.plan:
            return []
        
        expensive = []
        
        def walk(node: ExplainNode):
            if node.node_type == ScanType.SORT.value:
                if node.total_cost > threshold:
                    expensive.append(node)
            for child in node.children:
                walk(child)
        
        walk(self.plan)
        return expensive


@dataclass
class QuerySuggestion:
    """A suggestion for query optimization.
    
    Attributes:
        type: Type of suggestion
        table: Table the suggestion applies to
        columns: Columns involved (for index suggestions)
        message: Human-readable suggestion
        reason: Why this suggestion was made
        confidence: How confident we are (0-1)
        sql: Suggested SQL (e.g., CREATE INDEX)
    """
    type: SuggestionType
    table: Optional[str] = None
    columns: Tuple[str, ...] = ()
    message: str = ""
    reason: str = ""
    confidence: float = 1.0
    sql: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "table": self.table,
            "columns": list(self.columns),
            "message": self.message,
            "reason": self.reason,
            "confidence": self.confidence,
            "sql": self.sql,
        }


@dataclass
class AnalysisResult:
    """Result of query analysis.
    
    Contains all analysis results for a single query.
    
    Attributes:
        query: The analyzed query
        duration_ms: Query duration
        is_slow: Whether query exceeded slow threshold
        explain: EXPLAIN result (if analyzed)
        suggestions: List of suggestions
        query_type: Type of query (SELECT, INSERT, etc.)
        table: Main table involved
    """
    query: str
    duration_ms: float = 0.0
    is_slow: bool = False
    explain: Optional[ExplainResult] = None
    suggestions: List[QuerySuggestion] = field(default_factory=list)
    query_type: Optional[str] = None
    table: Optional[str] = None
    analyzed_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "duration_ms": self.duration_ms,
            "is_slow": self.is_slow,
            "explain": {
                "total_cost": self.explain.total_cost if self.explain else None,
                "execution_time": self.explain.execution_time if self.explain else None,
            },
            "suggestions": [s.to_dict() for s in self.suggestions],
            "query_type": self.query_type,
            "table": self.table,
        }


# ============================================================================
# Query Analyzer
# ============================================================================

class QueryAnalyzer:
    """Analyzer for database queries.
    
    Provides slow query detection, EXPLAIN analysis, and
    optimization suggestions.
    
    Example:
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=50))
        
        # Analyze a slow query
        result = await analyzer.analyze(
            query="SELECT * FROM users WHERE email = 'test@example.com'",
            duration_ms=200,
        )
        
        for suggestion in result.suggestions:
            print(suggestion.message)
    """
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        """Initialize analyzer.
        
        Args:
            config: Analyzer configuration
        """
        self.config = config or AnalyzerConfig()
        self._history: List[AnalysisResult] = []
        
        # Patterns for query parsing
        self._select_pattern = re.compile(
            r"SELECT\s+(.*?)\s+FROM\s+(\w+)",
            re.IGNORECASE | re.DOTALL,
        )
        self._where_pattern = re.compile(
            r"WHERE\s+(.+?)(?:\s+ORDER|\s+GROUP|\s+LIMIT|\s*$)",
            re.IGNORECASE | re.DOTALL,
        )
        self._order_pattern = re.compile(
            r"ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*$)",
            re.IGNORECASE | re.DOTALL,
        )
        self._limit_pattern = re.compile(
            r"LIMIT\s+(\d+)",
            re.IGNORECASE,
        )
    
    @property
    def enabled(self) -> bool:
        """Whether analysis is enabled."""
        return self.config.enabled
    
    def is_slow(self, duration_ms: float) -> bool:
        """Check if query duration is considered slow.
        
        Args:
            duration_ms: Query duration in milliseconds
        
        Returns:
            True if duration exceeds slow threshold
        """
        return duration_ms > self.config.slow_threshold_ms
    
    def analyze(
        self,
        query: str,
        duration_ms: float,
        explain_result: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Analyze a query.
        
        Args:
            query: The SQL query
            duration_ms: Query execution time
            explain_result: Optional EXPLAIN output (JSON format)
        
        Returns:
            Analysis result with suggestions
        """
        if not self.config.enabled:
            return AnalysisResult(query=query, duration_ms=duration_ms)
        
        # Parse query basics
        query_type = self._parse_query_type(query)
        table = self._parse_table(query, query_type)
        
        result = AnalysisResult(
            query=query,
            duration_ms=duration_ms,
            is_slow=self.is_slow(duration_ms),
            query_type=query_type,
            table=table,
        )
        
        # Parse EXPLAIN if provided
        if explain_result:
            result.explain = ExplainResult.from_json(explain_result)
        
        # Generate suggestions
        if result.is_slow or explain_result:
            self._generate_suggestions(result)
        
        # Store in history
        if self.config.store_history:
            self._add_to_history(result)
        
        # Callbacks
        if result.is_slow and self.config.on_slow_query:
            self.config.on_slow_query(result)
        
        return result
    
    def _parse_query_type(self, query: str) -> Optional[str]:
        """Extract query type from query text."""
        query_upper = query.strip().upper()
        for qt in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]:
            if query_upper.startswith(qt):
                return qt
        return None
    
    def _parse_table(self, query: str, query_type: Optional[str]) -> Optional[str]:
        """Extract main table from query."""
        query_upper = query.upper()
        
        if query_type == "SELECT":
            match = self._select_pattern.search(query)
            if match:
                return match.group(2).lower()
        elif query_type == "INSERT":
            if "INTO " in query_upper:
                parts = query_upper.split("INTO ", 1)
                if len(parts) > 1:
                    table = parts[1].split()[0] if parts[1].split() else None
                    return table.strip('("').lower() if table else None
        elif query_type == "UPDATE":
            parts = query_upper.split()
            if len(parts) > 1:
                return parts[1].strip('"').lower()
        elif query_type == "DELETE":
            if "FROM " in query_upper:
                parts = query_upper.split("FROM ", 1)
                if len(parts) > 1:
                    table = parts[1].split()[0] if parts[1].split() else None
                    return table.strip('("').lower() if table else None
        
        return None
    
    def _generate_suggestions(self, result: AnalysisResult) -> None:
        """Generate optimization suggestions."""
        suggestions = []
        
        # Check EXPLAIN for sequential scans
        if result.explain and self.config.suggest_indexes:
            suggestions.extend(self._suggest_indexes(result))
        
        # Check for query patterns
        if self.config.suggest_rewrites:
            suggestions.extend(self._suggest_rewrites(result))
        
        result.suggestions = suggestions
        
        # Callbacks
        for suggestion in suggestions:
            if self.config.on_suggestion:
                self.config.on_suggestion(suggestion)
    
    def _suggest_indexes(self, result: AnalysisResult) -> List[QuerySuggestion]:
        """Generate index suggestions from EXPLAIN output."""
        suggestions = []
        
        if not result.explain:
            return suggestions
        
        # Find sequential scans
        seq_scans = result.explain.find_seq_scans()
        
        for scan in seq_scans:
            # Try to extract columns from filter condition
            columns = self._extract_filter_columns(scan.filter)
            
            if columns and scan.relation:
                # Generate index suggestion
                index_name = f"idx_{scan.relation}_{'_'.join(columns)}"
                column_list = ", ".join(columns)
                
                suggestions.append(QuerySuggestion(
                    type=SuggestionType.INDEX,
                    table=scan.relation,
                    columns=tuple(columns),
                    message=f"Add index on {scan.relation}({column_list})",
                    reason=f"Seq Scan detected on {scan.relation} with filter",
                    confidence=0.8,
                    sql=f'CREATE INDEX {index_name} ON {scan.relation} ({column_list});',
                ))
        
        return suggestions
    
    def _suggest_rewrites(self, result: AnalysisResult) -> List[QuerySuggestion]:
        """Generate query rewrite suggestions."""
        suggestions = []
        query = result.query
        query_upper = query.upper()
        
        # Check for SELECT *
        if "SELECT *" in query_upper or "SELECT * " in query_upper:
            suggestions.append(QuerySuggestion(
                type=SuggestionType.SELECT_STAR,
                message="Consider selecting only needed columns instead of SELECT *",
                reason="SELECT * retrieves all columns which may be unnecessary",
                confidence=0.7,
            ))
        
        # Check for missing LIMIT on SELECT
        if result.query_type == "SELECT":
            if not self._limit_pattern.search(query):
                # Check if it looks like it returns many rows
                if result.explain and result.explain.plan:
                    if result.explain.plan.rows > 100:
                        suggestions.append(QuerySuggestion(
                            type=SuggestionType.LIMIT,
                            message="Consider adding LIMIT if not all rows are needed",
                            reason=f"Query returns ~{result.explain.plan.rows} rows",
                            confidence=0.6,
                        ))
        
        # Check for expensive sorts
        if result.explain:
            expensive_sorts = result.explain.find_expensive_sorts(100.0)
            for sort_node in expensive_sorts:
                suggestions.append(QuerySuggestion(
                    type=SuggestionType.SORT,
                    message="Consider adding index for ORDER BY columns or removing sort",
                    reason=f"Sort operation has high cost: {sort_node.total_cost}",
                    confidence=0.6,
                ))
        
        return suggestions
    
    def _extract_filter_columns(self, filter_expr: Optional[str]) -> List[str]:
        """Extract column names from a filter expression."""
        if not filter_expr:
            return []
        
        columns = []
        
        # Pattern to match column references like "column_name = ..."
        # This is simplified; real parsing would need SQL parser
        col_pattern = re.compile(r"(\w+)\s*(?:=|<|>|<=|>=|<>|!=|LIKE|IN)", re.IGNORECASE)
        
        for match in col_pattern.finditer(filter_expr):
            col = match.group(1).lower()
            # Filter out SQL keywords
            if col not in ("and", "or", "not", "null", "true", "false"):
                columns.append(col)
        
        return columns
    
    def _add_to_history(self, result: AnalysisResult) -> None:
        """Add result to history."""
        self._history.append(result)
        
        # Trim history
        if len(self._history) > self.config.history_size:
            self._history = self._history[-self.config.history_size:]
    
    def detect_n_plus_one(self, window_seconds: float = 1.0) -> List[QuerySuggestion]:
        """Detect N+1 query patterns from history.
        
        N+1 pattern: One query followed by N similar queries.
        Example:
            SELECT * FROM posts  -- 1 query
            SELECT * FROM users WHERE id = 1  -- N queries
            SELECT * FROM users WHERE id = 2
            SELECT * FROM users WHERE id = 3
            ...
        
        Args:
            window_seconds: Time window to look for patterns
        
        Returns:
            List of N+1 pattern suggestions
        """
        suggestions = []
        now = time.time()
        
        # Get recent queries
        recent = [
            r for r in self._history
            if now - r.analyzed_at < window_seconds
        ]
        
        if len(recent) < 3:
            return suggestions
        
        # Group by normalized query pattern
        patterns: Dict[str, int] = {}
        for r in recent:
            # Normalize query (replace values with ?)
            normalized = self._normalize_query(r.query)
            patterns[normalized] = patterns.get(normalized, 0) + 1
        
        # Find patterns with high repetition
        for pattern, count in patterns.items():
            if count >= 5:  # 5+ similar queries = likely N+1
                suggestions.append(QuerySuggestion(
                    type=SuggestionType.N_PLUS_ONE,
                    message=f"Possible N+1 query pattern detected ({count} similar queries)",
                    reason="Consider using eager loading or batch queries",
                    confidence=0.7,
                ))
        
        return suggestions
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching.
        
        Replaces literal values with placeholders.
        """
        # Replace string literals
        normalized = re.sub(r"'[^']*'", "'?'", query)
        # Replace numbers
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        # Normalize whitespace
        normalized = " ".join(normalized.split())
        return normalized.upper()
    
    def get_history(
        self,
        limit: int = 100,
        slow_only: bool = False,
    ) -> List[AnalysisResult]:
        """Get query history.
        
        Args:
            limit: Maximum results to return
            slow_only: Only return slow queries
        
        Returns:
            List of analysis results
        """
        results = self._history
        
        if slow_only:
            results = [r for r in results if r.is_slow]
        
        return results[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics.
        
        Returns:
            Dictionary with stats
        """
        slow_count = sum(1 for r in self._history if r.is_slow)
        
        return {
            "total_queries": len(self._history),
            "slow_queries": slow_count,
            "slow_percentage": (slow_count / len(self._history) * 100) if self._history else 0,
            "config": {
                "slow_threshold_ms": self.config.slow_threshold_ms,
                "auto_explain": self.config.auto_explain,
            },
        }
    
    def clear_history(self) -> None:
        """Clear query history."""
        self._history.clear()


# ============================================================================
# Convenience Functions
# ============================================================================

def create_analyzer(
    slow_threshold_ms: float = 100.0,
    suggest_indexes: bool = True,
    suggest_rewrites: bool = True,
    **kwargs: Any,
) -> QueryAnalyzer:
    """Create a query analyzer with common options.
    
    Args:
        slow_threshold_ms: Threshold for slow query detection
        suggest_indexes: Whether to suggest indexes
        suggest_rewrites: Whether to suggest rewrites
        **kwargs: Additional AnalyzerConfig options
    
    Returns:
        Configured QueryAnalyzer instance
    """
    config = AnalyzerConfig(
        slow_threshold_ms=slow_threshold_ms,
        suggest_indexes=suggest_indexes,
        suggest_rewrites=suggest_rewrites,
        **kwargs,
    )
    return QueryAnalyzer(config)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Configuration
    "AnalyzerConfig",
    "SuggestionType",
    "ScanType",
    
    # Data classes
    "ExplainNode",
    "ExplainResult",
    "QuerySuggestion",
    "AnalysisResult",
    
    # Analyzer
    "QueryAnalyzer",
    
    # Convenience
    "create_analyzer",
]

