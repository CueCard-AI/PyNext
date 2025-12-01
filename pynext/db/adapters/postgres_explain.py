"""
PyNext Query EXPLAIN/ANALYZE.

Provides comprehensive query plan analysis with:
- Raw EXPLAIN output
- Parsed structured data
- ASCII tree visualization
- Automatic optimization suggestions

Why This Matters:
    Understanding query plans is essential for performance optimization.
    PyNext makes this accessible with parsed output and suggestions.

Usage - Basic Explain:
    plan = await User.select().where(active=True).explain()
    print(plan.raw)          # Raw PostgreSQL output
    print(plan.cost)         # Estimated cost
    print(plan.rows)         # Estimated rows

Usage - With Analyze (Actually Executes):
    plan = await query.analyze()
    print(plan.actual_time)  # Real execution time
    print(plan.actual_rows)  # Real row count

Usage - Full Analysis:
    plan = await query.explain(analyze=True, buffers=True)
    print(plan.tree)         # ASCII visualization
    print(plan.suggestions)  # Optimization hints

Usage - Compare Plans:
    comparison = plan1.compare(plan2)
    print(comparison.summary)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
import json
import re
import textwrap


# =============================================================================
# ENUMS
# =============================================================================

class ExplainFormat(str, Enum):
    """Output format for EXPLAIN."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    TREE = "tree"  # Custom ASCII tree


class NodeType(str, Enum):
    """PostgreSQL plan node types."""
    SEQ_SCAN = "Seq Scan"
    INDEX_SCAN = "Index Scan"
    INDEX_ONLY_SCAN = "Index Only Scan"
    BITMAP_HEAP_SCAN = "Bitmap Heap Scan"
    BITMAP_INDEX_SCAN = "Bitmap Index Scan"
    NESTED_LOOP = "Nested Loop"
    HASH_JOIN = "Hash Join"
    MERGE_JOIN = "Merge Join"
    HASH = "Hash"
    SORT = "Sort"
    LIMIT = "Limit"
    AGGREGATE = "Aggregate"
    GROUP_AGGREGATE = "GroupAggregate"
    HASH_AGGREGATE = "HashAggregate"
    MATERIALIZE = "Materialize"
    SUBQUERY_SCAN = "Subquery Scan"
    CTE_SCAN = "CTE Scan"
    APPEND = "Append"
    MERGE_APPEND = "Merge Append"
    RESULT = "Result"
    GATHER = "Gather"
    GATHER_MERGE = "Gather Merge"
    UNKNOWN = "Unknown"


class SuggestionSeverity(str, Enum):
    """Severity of optimization suggestion."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class BufferStats:
    """
    Buffer I/O statistics from EXPLAIN ANALYZE BUFFERS.
    
    Attributes:
        shared_hit: Shared buffer hits
        shared_read: Shared buffer reads
        shared_dirtied: Shared buffers dirtied
        shared_written: Shared buffers written
        local_hit: Local buffer hits
        local_read: Local buffer reads
        temp_read: Temp buffers read
        temp_written: Temp buffers written
    """
    shared_hit: int = 0
    shared_read: int = 0
    shared_dirtied: int = 0
    shared_written: int = 0
    local_hit: int = 0
    local_read: int = 0
    temp_read: int = 0
    temp_written: int = 0
    
    @property
    def total_reads(self) -> int:
        """Total buffer reads (cache misses)."""
        return self.shared_read + self.local_read + self.temp_read
    
    @property
    def total_hits(self) -> int:
        """Total buffer hits (cache hits)."""
        return self.shared_hit + self.local_hit
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-100%)."""
        total = self.total_hits + self.total_reads
        if total == 0:
            return 100.0
        return (self.total_hits / total) * 100
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BufferStats":
        """Create from EXPLAIN JSON output."""
        return cls(
            shared_hit=data.get("Shared Hit Blocks", 0),
            shared_read=data.get("Shared Read Blocks", 0),
            shared_dirtied=data.get("Shared Dirtied Blocks", 0),
            shared_written=data.get("Shared Written Blocks", 0),
            local_hit=data.get("Local Hit Blocks", 0),
            local_read=data.get("Local Read Blocks", 0),
            temp_read=data.get("Temp Read Blocks", 0),
            temp_written=data.get("Temp Written Blocks", 0),
        )
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "shared_hit": self.shared_hit,
            "shared_read": self.shared_read,
            "shared_dirtied": self.shared_dirtied,
            "shared_written": self.shared_written,
            "local_hit": self.local_hit,
            "local_read": self.local_read,
            "temp_read": self.temp_read,
            "temp_written": self.temp_written,
            "total_reads": self.total_reads,
            "total_hits": self.total_hits,
            "hit_rate": self.hit_rate,
        }


@dataclass
class PlanNode:
    """
    Single node in the query execution tree.
    
    Attributes:
        node_type: Type of node (Seq Scan, Index Scan, etc.)
        relation: Table/index being accessed
        alias: Table alias
        startup_cost: Cost before returning first row
        total_cost: Total estimated cost
        rows: Estimated row count
        width: Average row width in bytes
        actual_startup_time: Real time to first row (ms)
        actual_total_time: Real total time (ms)
        actual_rows: Real row count
        actual_loops: Number of loop iterations
        filter: Filter condition (if any)
        index_cond: Index condition (if any)
        output: Output columns
        children: Child nodes
        buffers: Buffer stats (if BUFFERS enabled)
        workers_planned: Parallel workers planned
        workers_launched: Parallel workers launched
    """
    node_type: str
    relation: Optional[str] = None
    alias: Optional[str] = None
    startup_cost: float = 0.0
    total_cost: float = 0.0
    rows: int = 0
    width: int = 0
    actual_startup_time: Optional[float] = None
    actual_total_time: Optional[float] = None
    actual_rows: Optional[int] = None
    actual_loops: int = 1
    filter: Optional[str] = None
    index_cond: Optional[str] = None
    output: List[str] = field(default_factory=list)
    children: List["PlanNode"] = field(default_factory=list)
    buffers: Optional[BufferStats] = None
    workers_planned: int = 0
    workers_launched: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_scan(self) -> bool:
        """Check if this is a scan node."""
        return "Scan" in self.node_type
    
    @property
    def is_seq_scan(self) -> bool:
        """Check if this is a sequential scan."""
        return self.node_type == NodeType.SEQ_SCAN.value
    
    @property
    def is_index_scan(self) -> bool:
        """Check if this is an index scan."""
        return "Index" in self.node_type
    
    @property
    def is_join(self) -> bool:
        """Check if this is a join node."""
        return "Join" in self.node_type or "Nested Loop" in self.node_type
    
    @property
    def rows_removed_by_filter(self) -> int:
        """Rows removed by filter (if analyze data available)."""
        if self.actual_rows is not None and self.rows > 0:
            return max(0, self.rows - self.actual_rows)
        return 0
    
    @property
    def estimate_accuracy(self) -> Optional[float]:
        """How accurate was the row estimate (ratio)."""
        if self.actual_rows is None or self.actual_rows == 0:
            return None
        return self.rows / self.actual_rows
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanNode":
        """Create from EXPLAIN JSON output."""
        children = [
            cls.from_dict(child) 
            for child in data.get("Plans", [])
        ]
        
        buffers = None
        if any(k in data for k in ["Shared Hit Blocks", "Shared Read Blocks"]):
            buffers = BufferStats.from_dict(data)
        
        return cls(
            node_type=data.get("Node Type", "Unknown"),
            relation=data.get("Relation Name"),
            alias=data.get("Alias"),
            startup_cost=data.get("Startup Cost", 0),
            total_cost=data.get("Total Cost", 0),
            rows=data.get("Plan Rows", 0),
            width=data.get("Plan Width", 0),
            actual_startup_time=data.get("Actual Startup Time"),
            actual_total_time=data.get("Actual Total Time"),
            actual_rows=data.get("Actual Rows"),
            actual_loops=data.get("Actual Loops", 1),
            filter=data.get("Filter"),
            index_cond=data.get("Index Cond"),
            output=data.get("Output", []),
            children=children,
            buffers=buffers,
            workers_planned=data.get("Workers Planned", 0),
            workers_launched=data.get("Workers Launched", 0),
            extra={k: v for k, v in data.items() if k not in [
                "Node Type", "Relation Name", "Alias", "Startup Cost",
                "Total Cost", "Plan Rows", "Plan Width", "Actual Startup Time",
                "Actual Total Time", "Actual Rows", "Actual Loops", "Filter",
                "Index Cond", "Output", "Plans", "Workers Planned",
                "Workers Launched", "Shared Hit Blocks", "Shared Read Blocks",
            ]},
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "node_type": self.node_type,
            "startup_cost": self.startup_cost,
            "total_cost": self.total_cost,
            "rows": self.rows,
            "width": self.width,
        }
        
        if self.relation:
            result["relation"] = self.relation
        if self.alias:
            result["alias"] = self.alias
        if self.actual_startup_time is not None:
            result["actual_startup_time"] = self.actual_startup_time
        if self.actual_total_time is not None:
            result["actual_total_time"] = self.actual_total_time
        if self.actual_rows is not None:
            result["actual_rows"] = self.actual_rows
        if self.filter:
            result["filter"] = self.filter
        if self.index_cond:
            result["index_cond"] = self.index_cond
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.buffers:
            result["buffers"] = self.buffers.to_dict()
        
        return result


@dataclass
class Suggestion:
    """
    Optimization suggestion.
    
    Attributes:
        severity: How important is this suggestion
        title: Short title
        description: Detailed description
        action: Suggested action to take
        affected_node: Which node this applies to
    """
    severity: SuggestionSeverity
    title: str
    description: str
    action: Optional[str] = None
    affected_node: Optional[str] = None
    
    def __str__(self) -> str:
        prefix = {
            SuggestionSeverity.INFO: "ℹ️",
            SuggestionSeverity.WARNING: "⚠️",
            SuggestionSeverity.CRITICAL: "🚨",
        }.get(self.severity, "")
        return f"{prefix} {self.title}: {self.description}"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "action": self.action or "",
            "affected_node": self.affected_node or "",
        }


@dataclass
class QueryPlan:
    """
    Complete parsed query plan.
    
    Attributes:
        raw: Original EXPLAIN output
        format: Output format used
        query: Original query (if available)
        total_cost: Total estimated cost
        startup_cost: Cost before first row
        rows: Estimated row count
        width: Average row width
        actual_time: Real total time (analyze only)
        actual_rows: Real row count (analyze only)
        planning_time: Time spent planning (ms)
        execution_time: Time spent executing (ms)
        buffers: Buffer I/O statistics
        root_node: Root of execution tree
        suggestions: Optimization suggestions
        analyzed: Whether ANALYZE was used
        jit: JIT compilation info (if enabled)
    """
    raw: str
    format: ExplainFormat = ExplainFormat.TEXT
    query: Optional[str] = None
    total_cost: float = 0.0
    startup_cost: float = 0.0
    rows: int = 0
    width: int = 0
    actual_time: Optional[float] = None
    actual_rows: Optional[int] = None
    planning_time: Optional[float] = None
    execution_time: Optional[float] = None
    buffers: Optional[BufferStats] = None
    root_node: Optional[PlanNode] = None
    suggestions: List[Suggestion] = field(default_factory=list)
    analyzed: bool = False
    jit: Optional[Dict[str, Any]] = None
    
    @property
    def cost(self) -> float:
        """Alias for total_cost."""
        return self.total_cost
    
    @property
    def nodes(self) -> List[PlanNode]:
        """Flatten all nodes into a list."""
        if not self.root_node:
            return []
        
        result = []
        stack = [self.root_node]
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(node.children)
        return result
    
    @property
    def tree(self) -> str:
        """Generate ASCII tree visualization."""
        return self._generate_tree()
    
    @property
    def has_seq_scan(self) -> bool:
        """Check if plan contains sequential scans."""
        return any(n.is_seq_scan for n in self.nodes)
    
    @property
    def seq_scan_tables(self) -> List[str]:
        """Tables with sequential scans."""
        return [
            n.relation for n in self.nodes 
            if n.is_seq_scan and n.relation
        ]
    
    @property
    def total_buffer_reads(self) -> int:
        """Total buffer reads across all nodes."""
        return sum(
            n.buffers.total_reads for n in self.nodes 
            if n.buffers
        )
    
    def _generate_tree(self, node: Optional[PlanNode] = None, prefix: str = "", is_last: bool = True) -> str:
        """Generate ASCII tree representation."""
        if node is None:
            if self.root_node is None:
                return "(empty plan)"
            return self._generate_tree(self.root_node)
        
        # Build this node's line
        connector = "└── " if is_last else "├── "
        
        # Node info
        node_info = f"{node.node_type}"
        if node.relation:
            node_info += f" on {node.relation}"
        if node.alias and node.alias != node.relation:
            node_info += f" ({node.alias})"
        
        # Cost info
        cost_info = f"cost={node.startup_cost:.2f}..{node.total_cost:.2f}"
        cost_info += f" rows={node.rows}"
        
        # Actual info if available
        if node.actual_total_time is not None:
            cost_info += f" actual_time={node.actual_total_time:.3f}ms"
        if node.actual_rows is not None:
            cost_info += f" actual_rows={node.actual_rows}"
        
        line = f"{prefix}{connector}{node_info}\n"
        line += f"{prefix}{'    ' if is_last else '│   '}({cost_info})\n"
        
        # Add filter info
        if node.filter:
            line += f"{prefix}{'    ' if is_last else '│   '}Filter: {node.filter}\n"
        if node.index_cond:
            line += f"{prefix}{'    ' if is_last else '│   '}Index Cond: {node.index_cond}\n"
        
        # Recurse to children
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            line += self._generate_tree(child, child_prefix, is_last_child)
        
        return line
    
    def compare(self, other: "QueryPlan") -> "PlanComparison":
        """Compare this plan to another."""
        return PlanComparison.compare(self, other)
    
    @classmethod
    def from_json(cls, json_output: str, query: Optional[str] = None) -> "QueryPlan":
        """Parse from EXPLAIN (FORMAT JSON) output."""
        try:
            data = json.loads(json_output)
            if isinstance(data, list):
                if len(data) == 0:
                    return cls(raw=json_output, format=ExplainFormat.JSON, query=query)
                data = data[0]
            
            plan_data = data.get("Plan", data) if data else None
            
            root_node = PlanNode.from_dict(plan_data) if plan_data else None
            
            buffers = None
            if root_node and root_node.buffers:
                buffers = root_node.buffers
            
            instance = cls(
                raw=json_output,
                format=ExplainFormat.JSON,
                query=query,
                total_cost=plan_data.get("Total Cost", 0) if plan_data else 0,
                startup_cost=plan_data.get("Startup Cost", 0) if plan_data else 0,
                rows=plan_data.get("Plan Rows", 0) if plan_data else 0,
                width=plan_data.get("Plan Width", 0) if plan_data else 0,
                actual_time=plan_data.get("Actual Total Time") if plan_data else None,
                actual_rows=plan_data.get("Actual Rows") if plan_data else None,
                planning_time=data.get("Planning Time"),
                execution_time=data.get("Execution Time"),
                buffers=buffers,
                root_node=root_node,
                analyzed="Actual Rows" in (plan_data or {}),
                jit=data.get("JIT"),
            )
            
            # Generate suggestions
            instance.suggestions = PlanAnalyzer.analyze(instance)
            
            return instance
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return cls(raw=json_output, format=ExplainFormat.JSON, query=query)
    
    @classmethod
    def from_text(cls, text_output: str, query: Optional[str] = None) -> "QueryPlan":
        """Parse from EXPLAIN (FORMAT TEXT) output."""
        return ExplainTextParser.parse(text_output, query)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format": self.format.value,
            "query": self.query,
            "total_cost": self.total_cost,
            "startup_cost": self.startup_cost,
            "rows": self.rows,
            "width": self.width,
            "actual_time": self.actual_time,
            "actual_rows": self.actual_rows,
            "planning_time": self.planning_time,
            "execution_time": self.execution_time,
            "analyzed": self.analyzed,
            "has_seq_scan": self.has_seq_scan,
            "seq_scan_tables": self.seq_scan_tables,
            "root_node": self.root_node.to_dict() if self.root_node else None,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


@dataclass
class PlanComparison:
    """
    Comparison between two query plans.
    
    Attributes:
        plan1: First plan
        plan2: Second plan
        cost_diff: Difference in total cost
        cost_ratio: Ratio of costs (plan2/plan1)
        row_diff: Difference in estimated rows
        time_diff: Difference in actual time (if analyzed)
        better_plan: Which plan is better (1 or 2)
        summary: Human-readable summary
    """
    plan1: QueryPlan
    plan2: QueryPlan
    cost_diff: float = 0.0
    cost_ratio: float = 1.0
    row_diff: int = 0
    time_diff: Optional[float] = None
    better_plan: int = 0
    summary: str = ""
    
    @classmethod
    def compare(cls, plan1: QueryPlan, plan2: QueryPlan) -> "PlanComparison":
        """Compare two plans."""
        cost_diff = plan2.total_cost - plan1.total_cost
        cost_ratio = plan2.total_cost / plan1.total_cost if plan1.total_cost > 0 else 1.0
        row_diff = plan2.rows - plan1.rows
        
        time_diff = None
        if plan1.actual_time is not None and plan2.actual_time is not None:
            time_diff = plan2.actual_time - plan1.actual_time
        
        # Determine better plan (lower cost = better)
        if plan1.total_cost < plan2.total_cost:
            better_plan = 1
        elif plan2.total_cost < plan1.total_cost:
            better_plan = 2
        else:
            better_plan = 0  # Equal
        
        # Generate summary
        lines = []
        lines.append(f"Cost: {plan1.total_cost:.2f} vs {plan2.total_cost:.2f} ({cost_diff:+.2f})")
        lines.append(f"Rows: {plan1.rows} vs {plan2.rows} ({row_diff:+d})")
        
        if time_diff is not None:
            lines.append(f"Time: {plan1.actual_time:.3f}ms vs {plan2.actual_time:.3f}ms ({time_diff:+.3f}ms)")
        
        if better_plan == 1:
            lines.append("Plan 1 is better (lower cost)")
        elif better_plan == 2:
            lines.append("Plan 2 is better (lower cost)")
        else:
            lines.append("Plans are equivalent")
        
        summary = "\n".join(lines)
        
        return cls(
            plan1=plan1,
            plan2=plan2,
            cost_diff=cost_diff,
            cost_ratio=cost_ratio,
            row_diff=row_diff,
            time_diff=time_diff,
            better_plan=better_plan,
            summary=summary,
        )
    
    @property
    def is_plan1_better(self) -> bool:
        """Check if plan 1 is better."""
        return self.better_plan == 1
    
    @property
    def is_plan2_better(self) -> bool:
        """Check if plan 2 is better."""
        return self.better_plan == 2
    
    @property
    def improvement_percent(self) -> float:
        """Percentage improvement (positive = plan1 is better)."""
        if self.plan1.total_cost == 0:
            return 0.0
        return ((self.plan2.total_cost - self.plan1.total_cost) / self.plan1.total_cost) * 100


# =============================================================================
# PARSER
# =============================================================================

class ExplainTextParser:
    """Parse text format EXPLAIN output."""
    
    # Regex patterns for parsing text output
    COST_PATTERN = re.compile(r"cost=(\d+\.?\d*)\.\.(\d+\.?\d*)")
    ROWS_PATTERN = re.compile(r"rows=(\d+)")
    WIDTH_PATTERN = re.compile(r"width=(\d+)")
    ACTUAL_PATTERN = re.compile(r"actual time=(\d+\.?\d*)\.\.(\d+\.?\d*)")
    ACTUAL_ROWS_PATTERN = re.compile(r"rows=(\d+)")
    LOOPS_PATTERN = re.compile(r"loops=(\d+)")
    PLANNING_TIME_PATTERN = re.compile(r"Planning [Tt]ime: (\d+\.?\d*) ms")
    EXECUTION_TIME_PATTERN = re.compile(r"Execution [Tt]ime: (\d+\.?\d*) ms")
    NODE_PATTERN = re.compile(r"^\s*(->)?\s*([A-Za-z ]+)(?:\s+on\s+(\w+))?")
    
    @classmethod
    def parse(cls, text: str, query: Optional[str] = None) -> QueryPlan:
        """Parse text EXPLAIN output."""
        lines = text.strip().split("\n")
        
        # Extract planning and execution times
        planning_time = None
        execution_time = None
        
        for line in lines:
            if match := cls.PLANNING_TIME_PATTERN.search(line):
                planning_time = float(match.group(1))
            if match := cls.EXECUTION_TIME_PATTERN.search(line):
                execution_time = float(match.group(1))
        
        # Parse root node (first non-empty line)
        root_node = None
        total_cost = 0.0
        startup_cost = 0.0
        rows = 0
        width = 0
        actual_time = None
        actual_rows = None
        
        if lines:
            first_line = lines[0]
            
            # Extract costs
            if match := cls.COST_PATTERN.search(first_line):
                startup_cost = float(match.group(1))
                total_cost = float(match.group(2))
            
            if match := cls.ROWS_PATTERN.search(first_line):
                rows = int(match.group(1))
            
            if match := cls.WIDTH_PATTERN.search(first_line):
                width = int(match.group(1))
            
            if match := cls.ACTUAL_PATTERN.search(first_line):
                actual_time = float(match.group(2))
            
            # Parse node type
            node_type = "Unknown"
            relation = None
            
            # Common node types
            for nt in NodeType:
                if nt.value in first_line:
                    node_type = nt.value
                    break
            
            # Extract relation name
            if " on " in first_line:
                parts = first_line.split(" on ")
                if len(parts) > 1:
                    relation = parts[1].split()[0].strip("()")
            
            root_node = PlanNode(
                node_type=node_type,
                relation=relation,
                startup_cost=startup_cost,
                total_cost=total_cost,
                rows=rows,
                width=width,
                actual_total_time=actual_time,
            )
        
        analyzed = "actual time=" in text.lower() or "Execution Time:" in text
        
        plan = QueryPlan(
            raw=text,
            format=ExplainFormat.TEXT,
            query=query,
            total_cost=total_cost,
            startup_cost=startup_cost,
            rows=rows,
            width=width,
            actual_time=actual_time,
            actual_rows=actual_rows,
            planning_time=planning_time,
            execution_time=execution_time,
            root_node=root_node,
            analyzed=analyzed,
        )
        
        # Generate suggestions
        plan.suggestions = PlanAnalyzer.analyze(plan)
        
        return plan


# =============================================================================
# ANALYZER
# =============================================================================

class PlanAnalyzer:
    """
    Analyze query plans and generate optimization suggestions.
    """
    
    # Thresholds for suggestions
    SEQ_SCAN_ROW_THRESHOLD = 1000
    COST_THRESHOLD = 10000
    ROW_ESTIMATE_RATIO_THRESHOLD = 10
    BUFFER_READ_THRESHOLD = 1000
    
    @classmethod
    def analyze(cls, plan: QueryPlan) -> List[Suggestion]:
        """Analyze plan and generate suggestions."""
        suggestions = []
        
        # Check for sequential scans on large tables
        suggestions.extend(cls._check_seq_scans(plan))
        
        # Check for missing indexes
        suggestions.extend(cls._check_missing_indexes(plan))
        
        # Check for row estimate accuracy
        suggestions.extend(cls._check_row_estimates(plan))
        
        # Check for high costs
        suggestions.extend(cls._check_high_costs(plan))
        
        # Check buffer stats
        suggestions.extend(cls._check_buffer_stats(plan))
        
        # Check for sorts without indexes
        suggestions.extend(cls._check_sorts(plan))
        
        return suggestions
    
    @classmethod
    def _check_seq_scans(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check for problematic sequential scans."""
        suggestions = []
        
        for node in plan.nodes:
            if node.is_seq_scan and node.rows > cls.SEQ_SCAN_ROW_THRESHOLD:
                suggestions.append(Suggestion(
                    severity=SuggestionSeverity.WARNING,
                    title=f"Sequential scan on {node.relation}",
                    description=(
                        f"Full table scan on {node.relation} with ~{node.rows} rows. "
                        "This may be slow for large tables."
                    ),
                    action=f"Consider adding an index on {node.relation} for filtered columns.",
                    affected_node=node.node_type,
                ))
        
        return suggestions
    
    @classmethod
    def _check_missing_indexes(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check for potential missing indexes."""
        suggestions = []
        
        for node in plan.nodes:
            if node.is_seq_scan and node.filter:
                # Extract column from filter
                filter_str = node.filter
                
                suggestions.append(Suggestion(
                    severity=SuggestionSeverity.INFO,
                    title=f"Consider index for filter on {node.relation}",
                    description=(
                        f"Filter '{filter_str}' on sequential scan suggests "
                        "a potential index opportunity."
                    ),
                    action=f"CREATE INDEX ON {node.relation} (<filtered_column>)",
                    affected_node=node.node_type,
                ))
        
        return suggestions
    
    @classmethod
    def _check_row_estimates(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check for inaccurate row estimates."""
        suggestions = []
        
        for node in plan.nodes:
            if node.estimate_accuracy is not None:
                ratio = node.estimate_accuracy
                if ratio > cls.ROW_ESTIMATE_RATIO_THRESHOLD or ratio < 1/cls.ROW_ESTIMATE_RATIO_THRESHOLD:
                    suggestions.append(Suggestion(
                        severity=SuggestionSeverity.WARNING,
                        title=f"Inaccurate row estimate on {node.node_type}",
                        description=(
                            f"Estimated {node.rows} rows but got {node.actual_rows}. "
                            f"Estimate was off by {ratio:.1f}x."
                        ),
                        action="Run ANALYZE on the table to update statistics.",
                        affected_node=node.node_type,
                    ))
        
        return suggestions
    
    @classmethod
    def _check_high_costs(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check for high-cost nodes."""
        suggestions = []
        
        for node in plan.nodes:
            if node.total_cost > cls.COST_THRESHOLD:
                suggestions.append(Suggestion(
                    severity=SuggestionSeverity.INFO,
                    title=f"High cost on {node.node_type}",
                    description=(
                        f"Node has cost {node.total_cost:.0f} which is above threshold."
                    ),
                    affected_node=node.node_type,
                ))
        
        return suggestions
    
    @classmethod
    def _check_buffer_stats(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check buffer I/O statistics."""
        suggestions = []
        
        for node in plan.nodes:
            if node.buffers and node.buffers.total_reads > cls.BUFFER_READ_THRESHOLD:
                suggestions.append(Suggestion(
                    severity=SuggestionSeverity.WARNING,
                    title=f"High buffer reads on {node.node_type}",
                    description=(
                        f"Node read {node.buffers.total_reads} blocks from disk. "
                        f"Cache hit rate: {node.buffers.hit_rate:.1f}%"
                    ),
                    action="Consider increasing shared_buffers or adding indexes.",
                    affected_node=node.node_type,
                ))
        
        return suggestions
    
    @classmethod
    def _check_sorts(cls, plan: QueryPlan) -> List[Suggestion]:
        """Check for in-memory sorts."""
        suggestions = []
        
        for node in plan.nodes:
            if node.node_type == NodeType.SORT.value:
                # Check if sorting on a column that could use an index
                sort_key = node.extra.get("Sort Key", [])
                
                suggestions.append(Suggestion(
                    severity=SuggestionSeverity.INFO,
                    title="Sort operation",
                    description=(
                        f"Sorting {node.rows} rows. "
                        "An index might eliminate this sort."
                    ),
                    action="Consider adding a covering index for the ORDER BY columns.",
                    affected_node=node.node_type,
                ))
        
        return suggestions


# =============================================================================
# QUERY BUILDER MIXIN
# =============================================================================

T = TypeVar("T")


class ExplainMixin(Generic[T]):
    """
    Mixin for adding EXPLAIN/ANALYZE support to query builders.
    """
    
    async def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        costs: bool = True,
        buffers: bool = False,
        timing: bool = True,
        format: ExplainFormat = ExplainFormat.JSON,
    ) -> QueryPlan:
        """
        Get the execution plan for this query.
        
        Args:
            analyze: Actually execute the query (gets real times)
            verbose: Show additional info
            costs: Include cost estimates
            buffers: Show buffer usage (requires analyze)
            timing: Show timing info (requires analyze)
            format: Output format
        
        Returns:
            QueryPlan with parsed output
        
        Example:
            plan = await User.select().where(active=True).explain()
            print(plan.cost)
            print(plan.suggestions)
            
            # With analyze (actually runs query)
            plan = await query.explain(analyze=True, buffers=True)
            print(plan.actual_time)
        """
        # Build EXPLAIN options
        options = []
        if analyze:
            options.append("ANALYZE")
        if verbose:
            options.append("VERBOSE")
        if costs:
            options.append("COSTS")
        if buffers:
            options.append("BUFFERS")
        if timing and analyze:
            options.append("TIMING")
        options.append(f"FORMAT {format.value.upper()}")
        
        options_str = ", ".join(options)
        
        # This is a template - actual implementation depends on query builder
        # The query builder would override _get_sql() and _execute()
        sql = self._get_sql() if hasattr(self, "_get_sql") else ""
        explain_sql = f"EXPLAIN ({options_str}) {sql}"
        
        # Execute and parse
        if hasattr(self, "_execute_explain"):
            result = await self._execute_explain(explain_sql)
        else:
            result = ""
        
        # Parse based on format
        if format == ExplainFormat.JSON:
            return QueryPlan.from_json(result, query=sql)
        else:
            return QueryPlan.from_text(result, query=sql)
    
    async def analyze(
        self,
        buffers: bool = True,
        timing: bool = True,
    ) -> QueryPlan:
        """
        Execute query and get actual execution statistics.
        
        This is a shortcut for explain(analyze=True).
        
        Args:
            buffers: Include buffer stats
            timing: Include timing info
        
        Returns:
            QueryPlan with actual execution data
        
        Example:
            plan = await User.select().analyze()
            print(f"Took {plan.actual_time}ms")
            print(f"Returned {plan.actual_rows} rows")
        """
        return await self.explain(
            analyze=True,
            buffers=buffers,
            timing=timing,
        )


# =============================================================================
# EXPLAIN EXECUTOR
# =============================================================================

class ExplainExecutor:
    """
    Executes EXPLAIN queries.
    """
    
    def __init__(self, execute_fn: Callable = None):
        self._execute_fn = execute_fn
    
    def build_explain_sql(
        self,
        query: str,
        analyze: bool = False,
        verbose: bool = False,
        costs: bool = True,
        buffers: bool = False,
        timing: bool = True,
        format: ExplainFormat = ExplainFormat.JSON,
    ) -> str:
        """Build EXPLAIN SQL statement."""
        options = []
        
        if analyze:
            options.append("ANALYZE")
        if verbose:
            options.append("VERBOSE")
        if costs:
            options.append("COSTS")
        if buffers:
            options.append("BUFFERS")
        if timing and analyze:
            options.append("TIMING")
        
        options.append(f"FORMAT {format.value.upper()}")
        
        options_str = ", ".join(options)
        return f"EXPLAIN ({options_str}) {query}"
    
    async def explain(
        self,
        query: str,
        params: tuple = (),
        analyze: bool = False,
        buffers: bool = False,
        format: ExplainFormat = ExplainFormat.JSON,
    ) -> QueryPlan:
        """Execute EXPLAIN and return parsed plan."""
        explain_sql = self.build_explain_sql(
            query,
            analyze=analyze,
            buffers=buffers,
            format=format,
        )
        
        if self._execute_fn:
            result = await self._execute_fn(explain_sql, params)
        else:
            result = ""
        
        if format == ExplainFormat.JSON:
            return QueryPlan.from_json(result, query=query)
        else:
            return QueryPlan.from_text(result, query=query)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ExplainFormat",
    "NodeType",
    "SuggestionSeverity",
    # Data models
    "BufferStats",
    "PlanNode",
    "Suggestion",
    "QueryPlan",
    "PlanComparison",
    # Parser
    "ExplainTextParser",
    # Analyzer
    "PlanAnalyzer",
    # Mixin
    "ExplainMixin",
    # Executor
    "ExplainExecutor",
]

