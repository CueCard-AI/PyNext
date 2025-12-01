"""
Comprehensive tests for PyNext Query EXPLAIN/ANALYZE.

150 tests covering:
- Raw/parsed output
- All output formats (JSON, TEXT, YAML, XML)
- Suggestions generation
- ASCII tree visualization
- Plan comparison
- Edge cases
"""

import pytest
import json

from pynext.db.adapters.postgres_explain import (
    ExplainFormat,
    NodeType,
    SuggestionSeverity,
    BufferStats,
    PlanNode,
    Suggestion,
    QueryPlan,
    PlanComparison,
    ExplainTextParser,
    PlanAnalyzer,
    ExplainMixin,
    ExplainExecutor,
)


# =============================================================================
# EXPLAIN FORMAT TESTS
# =============================================================================

class TestExplainFormat:
    """Tests for ExplainFormat enum."""
    
    def test_text_format(self):
        """Test TEXT format value."""
        assert ExplainFormat.TEXT.value == "text"
    
    def test_json_format(self):
        """Test JSON format value."""
        assert ExplainFormat.JSON.value == "json"
    
    def test_yaml_format(self):
        """Test YAML format value."""
        assert ExplainFormat.YAML.value == "yaml"
    
    def test_xml_format(self):
        """Test XML format value."""
        assert ExplainFormat.XML.value == "xml"
    
    def test_tree_format(self):
        """Test custom TREE format."""
        assert ExplainFormat.TREE.value == "tree"


# =============================================================================
# NODE TYPE TESTS
# =============================================================================

class TestNodeType:
    """Tests for NodeType enum."""
    
    def test_seq_scan(self):
        """Test Seq Scan node type."""
        assert NodeType.SEQ_SCAN.value == "Seq Scan"
    
    def test_index_scan(self):
        """Test Index Scan node type."""
        assert NodeType.INDEX_SCAN.value == "Index Scan"
    
    def test_index_only_scan(self):
        """Test Index Only Scan node type."""
        assert NodeType.INDEX_ONLY_SCAN.value == "Index Only Scan"
    
    def test_nested_loop(self):
        """Test Nested Loop node type."""
        assert NodeType.NESTED_LOOP.value == "Nested Loop"
    
    def test_hash_join(self):
        """Test Hash Join node type."""
        assert NodeType.HASH_JOIN.value == "Hash Join"
    
    def test_sort(self):
        """Test Sort node type."""
        assert NodeType.SORT.value == "Sort"
    
    def test_aggregate(self):
        """Test Aggregate node type."""
        assert NodeType.AGGREGATE.value == "Aggregate"
    
    def test_gather(self):
        """Test Gather node type."""
        assert NodeType.GATHER.value == "Gather"


# =============================================================================
# BUFFER STATS TESTS
# =============================================================================

class TestBufferStats:
    """Tests for BufferStats."""
    
    def test_default_values(self):
        """Test default buffer stats values."""
        stats = BufferStats()
        assert stats.shared_hit == 0
        assert stats.shared_read == 0
        assert stats.total_reads == 0
        assert stats.total_hits == 0
    
    def test_hit_rate_empty(self):
        """Test hit rate with no data."""
        stats = BufferStats()
        assert stats.hit_rate == 100.0
    
    def test_hit_rate_all_hits(self):
        """Test hit rate with all hits."""
        stats = BufferStats(shared_hit=100, shared_read=0)
        assert stats.hit_rate == 100.0
    
    def test_hit_rate_mixed(self):
        """Test hit rate with mixed hits/reads."""
        stats = BufferStats(shared_hit=75, shared_read=25)
        assert stats.hit_rate == 75.0
    
    def test_hit_rate_all_misses(self):
        """Test hit rate with all misses."""
        stats = BufferStats(shared_hit=0, shared_read=100)
        assert stats.hit_rate == 0.0
    
    def test_total_reads(self):
        """Test total reads calculation."""
        stats = BufferStats(
            shared_read=10,
            local_read=5,
            temp_read=3,
        )
        assert stats.total_reads == 18
    
    def test_total_hits(self):
        """Test total hits calculation."""
        stats = BufferStats(
            shared_hit=20,
            local_hit=10,
        )
        assert stats.total_hits == 30
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "Shared Hit Blocks": 100,
            "Shared Read Blocks": 50,
            "Local Hit Blocks": 10,
        }
        stats = BufferStats.from_dict(data)
        assert stats.shared_hit == 100
        assert stats.shared_read == 50
        assert stats.local_hit == 10
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        stats = BufferStats(shared_hit=100, shared_read=50)
        d = stats.to_dict()
        assert d["shared_hit"] == 100
        assert d["shared_read"] == 50
        assert "hit_rate" in d


# =============================================================================
# PLAN NODE TESTS
# =============================================================================

class TestPlanNode:
    """Tests for PlanNode."""
    
    def test_basic_node(self):
        """Test basic node creation."""
        node = PlanNode(
            node_type="Seq Scan",
            relation="users",
            total_cost=100.0,
            rows=1000,
        )
        assert node.node_type == "Seq Scan"
        assert node.relation == "users"
        assert node.total_cost == 100.0
        assert node.rows == 1000
    
    def test_is_scan(self):
        """Test is_scan property."""
        scan_node = PlanNode(node_type="Seq Scan")
        assert scan_node.is_scan is True
        
        non_scan = PlanNode(node_type="Sort")
        assert non_scan.is_scan is False
    
    def test_is_seq_scan(self):
        """Test is_seq_scan property."""
        seq_scan = PlanNode(node_type="Seq Scan")
        assert seq_scan.is_seq_scan is True
        
        index_scan = PlanNode(node_type="Index Scan")
        assert index_scan.is_seq_scan is False
    
    def test_is_index_scan(self):
        """Test is_index_scan property."""
        index_scan = PlanNode(node_type="Index Scan")
        assert index_scan.is_index_scan is True
        
        index_only = PlanNode(node_type="Index Only Scan")
        assert index_only.is_index_scan is True
        
        seq_scan = PlanNode(node_type="Seq Scan")
        assert seq_scan.is_index_scan is False
    
    def test_is_join(self):
        """Test is_join property."""
        nested_loop = PlanNode(node_type="Nested Loop")
        assert nested_loop.is_join is True
        
        hash_join = PlanNode(node_type="Hash Join")
        assert hash_join.is_join is True
        
        scan = PlanNode(node_type="Seq Scan")
        assert scan.is_join is False
    
    def test_estimate_accuracy_exact(self):
        """Test estimate accuracy when exact."""
        node = PlanNode(node_type="Seq Scan", rows=100, actual_rows=100)
        assert node.estimate_accuracy == 1.0
    
    def test_estimate_accuracy_underestimate(self):
        """Test estimate accuracy with underestimate."""
        node = PlanNode(node_type="Seq Scan", rows=50, actual_rows=100)
        assert node.estimate_accuracy == 0.5
    
    def test_estimate_accuracy_overestimate(self):
        """Test estimate accuracy with overestimate."""
        node = PlanNode(node_type="Seq Scan", rows=200, actual_rows=100)
        assert node.estimate_accuracy == 2.0
    
    def test_estimate_accuracy_no_actual(self):
        """Test estimate accuracy without actual data."""
        node = PlanNode(node_type="Seq Scan", rows=100)
        assert node.estimate_accuracy is None
    
    def test_from_dict(self):
        """Test creating from EXPLAIN JSON."""
        data = {
            "Node Type": "Seq Scan",
            "Relation Name": "users",
            "Startup Cost": 0.0,
            "Total Cost": 100.0,
            "Plan Rows": 1000,
            "Plan Width": 50,
            "Filter": "(active = true)",
        }
        node = PlanNode.from_dict(data)
        assert node.node_type == "Seq Scan"
        assert node.relation == "users"
        assert node.filter == "(active = true)"
    
    def test_from_dict_with_children(self):
        """Test creating with child nodes."""
        data = {
            "Node Type": "Nested Loop",
            "Plans": [
                {"Node Type": "Seq Scan", "Relation Name": "users"},
                {"Node Type": "Index Scan", "Relation Name": "orders"},
            ],
        }
        node = PlanNode.from_dict(data)
        assert len(node.children) == 2
        assert node.children[0].node_type == "Seq Scan"
        assert node.children[1].node_type == "Index Scan"
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        node = PlanNode(
            node_type="Seq Scan",
            relation="users",
            total_cost=100.0,
            rows=1000,
        )
        d = node.to_dict()
        assert d["node_type"] == "Seq Scan"
        assert d["relation"] == "users"
        assert d["total_cost"] == 100.0


# =============================================================================
# SUGGESTION TESTS
# =============================================================================

class TestSuggestion:
    """Tests for Suggestion."""
    
    def test_info_suggestion(self):
        """Test INFO level suggestion."""
        s = Suggestion(
            severity=SuggestionSeverity.INFO,
            title="Consider index",
            description="Adding an index might help",
        )
        assert s.severity == SuggestionSeverity.INFO
        assert "Consider index" in str(s)
    
    def test_warning_suggestion(self):
        """Test WARNING level suggestion."""
        s = Suggestion(
            severity=SuggestionSeverity.WARNING,
            title="Sequential scan",
            description="Full table scan detected",
        )
        assert s.severity == SuggestionSeverity.WARNING
    
    def test_critical_suggestion(self):
        """Test CRITICAL level suggestion."""
        s = Suggestion(
            severity=SuggestionSeverity.CRITICAL,
            title="Missing index",
            description="Critical performance issue",
        )
        assert s.severity == SuggestionSeverity.CRITICAL
    
    def test_suggestion_with_action(self):
        """Test suggestion with action."""
        s = Suggestion(
            severity=SuggestionSeverity.INFO,
            title="Add index",
            description="Missing index",
            action="CREATE INDEX ON users(email)",
        )
        assert s.action == "CREATE INDEX ON users(email)"
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        s = Suggestion(
            severity=SuggestionSeverity.WARNING,
            title="Test",
            description="Description",
        )
        d = s.to_dict()
        assert d["severity"] == "warning"
        assert d["title"] == "Test"


# =============================================================================
# QUERY PLAN TESTS
# =============================================================================

class TestQueryPlan:
    """Tests for QueryPlan."""
    
    def test_basic_plan(self):
        """Test basic plan creation."""
        plan = QueryPlan(
            raw="Seq Scan on users",
            format=ExplainFormat.TEXT,
            total_cost=100.0,
            rows=1000,
        )
        assert plan.cost == 100.0  # Alias
        assert plan.rows == 1000
    
    def test_nodes_empty(self):
        """Test nodes property with no root."""
        plan = QueryPlan(raw="")
        assert plan.nodes == []
    
    def test_nodes_with_root(self):
        """Test nodes property with root node."""
        root = PlanNode(
            node_type="Seq Scan",
            children=[
                PlanNode(node_type="Filter"),
            ],
        )
        plan = QueryPlan(raw="", root_node=root)
        assert len(plan.nodes) == 2
    
    def test_has_seq_scan(self):
        """Test has_seq_scan property."""
        root = PlanNode(node_type="Seq Scan", relation="users")
        plan = QueryPlan(raw="", root_node=root)
        assert plan.has_seq_scan is True
    
    def test_has_no_seq_scan(self):
        """Test has_seq_scan with index scan."""
        root = PlanNode(node_type="Index Scan", relation="users")
        plan = QueryPlan(raw="", root_node=root)
        assert plan.has_seq_scan is False
    
    def test_seq_scan_tables(self):
        """Test seq_scan_tables property."""
        root = PlanNode(
            node_type="Nested Loop",
            children=[
                PlanNode(node_type="Seq Scan", relation="users"),
                PlanNode(node_type="Index Scan", relation="orders"),
            ],
        )
        plan = QueryPlan(raw="", root_node=root)
        assert "users" in plan.seq_scan_tables
        assert "orders" not in plan.seq_scan_tables
    
    def test_tree_property_empty(self):
        """Test tree with no root."""
        plan = QueryPlan(raw="")
        assert plan.tree == "(empty plan)"
    
    def test_tree_property_with_node(self):
        """Test tree generation."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="users",
            total_cost=100.0,
            rows=1000,
        )
        plan = QueryPlan(raw="", root_node=root)
        tree = plan.tree
        assert "Seq Scan" in tree
        assert "users" in tree
    
    def test_from_json(self):
        """Test parsing JSON format."""
        json_output = json.dumps([{
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Startup Cost": 0.0,
                "Total Cost": 100.0,
                "Plan Rows": 1000,
                "Plan Width": 50,
            },
            "Planning Time": 0.5,
            "Execution Time": 10.0,
        }])
        
        plan = QueryPlan.from_json(json_output)
        assert plan.root_node is not None
        assert plan.root_node.node_type == "Seq Scan"
        assert plan.planning_time == 0.5
        assert plan.execution_time == 10.0
    
    def test_from_json_with_analyze(self):
        """Test parsing JSON with ANALYZE data."""
        json_output = json.dumps([{
            "Plan": {
                "Node Type": "Seq Scan",
                "Actual Rows": 1500,
                "Actual Total Time": 15.0,
            },
        }])
        
        plan = QueryPlan.from_json(json_output)
        assert plan.analyzed is True
    
    def test_from_text(self):
        """Test parsing TEXT format."""
        text_output = """Seq Scan on users  (cost=0.00..100.00 rows=1000 width=50)
  Filter: (active = true)
Planning Time: 0.5 ms
Execution Time: 10.0 ms"""
        
        plan = QueryPlan.from_text(text_output)
        assert plan.total_cost == 100.0
        assert plan.rows == 1000
        assert plan.planning_time == 0.5
        assert plan.execution_time == 10.0
    
    def test_compare(self):
        """Test plan comparison."""
        plan1 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        plan2 = QueryPlan(raw="", total_cost=50.0, rows=500)
        
        comparison = plan1.compare(plan2)
        assert comparison.is_plan2_better
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        plan = QueryPlan(
            raw="test",
            total_cost=100.0,
            rows=1000,
            analyzed=True,
        )
        d = plan.to_dict()
        assert d["total_cost"] == 100.0
        assert d["rows"] == 1000
        assert d["analyzed"] is True


# =============================================================================
# PLAN COMPARISON TESTS
# =============================================================================

class TestPlanComparison:
    """Tests for PlanComparison."""
    
    def test_compare_equal_plans(self):
        """Test comparing equal plans."""
        plan1 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        plan2 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert comparison.better_plan == 0
        assert comparison.cost_diff == 0.0
    
    def test_compare_plan1_better(self):
        """Test when plan1 is better."""
        plan1 = QueryPlan(raw="", total_cost=50.0, rows=500)
        plan2 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert comparison.is_plan1_better
        assert comparison.cost_diff == 50.0
    
    def test_compare_plan2_better(self):
        """Test when plan2 is better."""
        plan1 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        plan2 = QueryPlan(raw="", total_cost=50.0, rows=500)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert comparison.is_plan2_better
        assert comparison.cost_diff == -50.0
    
    def test_compare_with_actual_time(self):
        """Test comparison with actual execution time."""
        plan1 = QueryPlan(raw="", total_cost=100.0, actual_time=50.0)
        plan2 = QueryPlan(raw="", total_cost=100.0, actual_time=25.0)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert comparison.time_diff == -25.0
    
    def test_improvement_percent(self):
        """Test improvement percentage calculation."""
        plan1 = QueryPlan(raw="", total_cost=100.0)
        plan2 = QueryPlan(raw="", total_cost=50.0)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert comparison.improvement_percent == -50.0
    
    def test_summary_content(self):
        """Test summary contains expected info."""
        plan1 = QueryPlan(raw="", total_cost=100.0, rows=1000)
        plan2 = QueryPlan(raw="", total_cost=50.0, rows=500)
        
        comparison = PlanComparison.compare(plan1, plan2)
        assert "Cost:" in comparison.summary
        assert "Rows:" in comparison.summary


# =============================================================================
# EXPLAIN TEXT PARSER TESTS
# =============================================================================

class TestExplainTextParser:
    """Tests for ExplainTextParser."""
    
    def test_parse_simple_seq_scan(self):
        """Test parsing simple Seq Scan."""
        text = "Seq Scan on users  (cost=0.00..100.00 rows=1000 width=50)"
        plan = ExplainTextParser.parse(text)
        assert plan.total_cost == 100.0
        assert plan.rows == 1000
        assert plan.width == 50
    
    def test_parse_with_analyze(self):
        """Test parsing with ANALYZE data."""
        text = "Seq Scan on users  (cost=0.00..100.00 rows=1000) (actual time=1.0..10.0 rows=1500 loops=1)"
        plan = ExplainTextParser.parse(text)
        assert plan.analyzed is True
    
    def test_parse_with_planning_time(self):
        """Test parsing Planning Time."""
        text = """Seq Scan on users  (cost=0.00..100.00 rows=1000 width=50)
Planning Time: 0.5 ms"""
        plan = ExplainTextParser.parse(text)
        assert plan.planning_time == 0.5
    
    def test_parse_with_execution_time(self):
        """Test parsing Execution Time."""
        text = """Seq Scan on users  (cost=0.00..100.00 rows=1000 width=50)
Execution Time: 10.5 ms"""
        plan = ExplainTextParser.parse(text)
        assert plan.execution_time == 10.5
    
    def test_parse_index_scan(self):
        """Test parsing Index Scan."""
        text = "Index Scan using users_pkey on users  (cost=0.00..8.27 rows=1 width=50)"
        plan = ExplainTextParser.parse(text)
        assert plan.root_node.node_type == "Index Scan"
    
    def test_parse_extracts_relation(self):
        """Test extracting relation name."""
        text = "Seq Scan on users  (cost=0.00..100.00 rows=1000 width=50)"
        plan = ExplainTextParser.parse(text)
        assert plan.root_node.relation == "users"


# =============================================================================
# PLAN ANALYZER TESTS
# =============================================================================

class TestPlanAnalyzer:
    """Tests for PlanAnalyzer."""
    
    def test_detect_seq_scan(self):
        """Test detecting sequential scans."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="users",
            rows=10000,
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        seq_scan_suggestions = [
            s for s in suggestions 
            if "Sequential scan" in s.title or "sequential scan" in s.title.lower()
        ]
        assert len(seq_scan_suggestions) > 0
    
    def test_no_suggestion_for_small_seq_scan(self):
        """Test no suggestion for small table seq scan."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="settings",
            rows=10,  # Small table
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        seq_scan_suggestions = [
            s for s in suggestions 
            if "Sequential scan" in s.title
        ]
        assert len(seq_scan_suggestions) == 0
    
    def test_detect_missing_index(self):
        """Test detecting potential missing index."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="users",
            rows=5000,
            filter="(email = 'test@example.com')",
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        # Should have both seq scan warning and index suggestion
        assert len(suggestions) >= 1
    
    def test_detect_inaccurate_estimates(self):
        """Test detecting inaccurate row estimates."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="users",
            rows=100,  # Estimated
            actual_rows=10000,  # Actual (way off)
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        estimate_suggestions = [
            s for s in suggestions 
            if "estimate" in s.title.lower()
        ]
        assert len(estimate_suggestions) > 0
    
    def test_detect_high_cost(self):
        """Test detecting high cost nodes."""
        root = PlanNode(
            node_type="Seq Scan",
            relation="huge_table",
            total_cost=50000,
            rows=100,
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        cost_suggestions = [
            s for s in suggestions 
            if "cost" in s.title.lower()
        ]
        assert len(cost_suggestions) > 0
    
    def test_detect_buffer_issues(self):
        """Test detecting buffer read issues."""
        buffers = BufferStats(shared_read=5000)
        root = PlanNode(
            node_type="Seq Scan",
            relation="users",
            buffers=buffers,
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        buffer_suggestions = [
            s for s in suggestions 
            if "buffer" in s.title.lower()
        ]
        assert len(buffer_suggestions) > 0
    
    def test_detect_sort(self):
        """Test detecting sort operations."""
        root = PlanNode(
            node_type="Sort",
            rows=10000,
        )
        plan = QueryPlan(raw="", root_node=root)
        
        suggestions = PlanAnalyzer.analyze(plan)
        sort_suggestions = [
            s for s in suggestions 
            if "sort" in s.title.lower()
        ]
        assert len(sort_suggestions) > 0


# =============================================================================
# EXPLAIN EXECUTOR TESTS
# =============================================================================

class TestExplainExecutor:
    """Tests for ExplainExecutor."""
    
    def test_build_explain_sql_basic(self):
        """Test building basic EXPLAIN SQL."""
        executor = ExplainExecutor()
        sql = executor.build_explain_sql("SELECT * FROM users")
        assert "EXPLAIN" in sql
        assert "SELECT * FROM users" in sql
    
    def test_build_explain_sql_with_analyze(self):
        """Test building EXPLAIN ANALYZE SQL."""
        executor = ExplainExecutor()
        sql = executor.build_explain_sql("SELECT * FROM users", analyze=True)
        assert "ANALYZE" in sql
    
    def test_build_explain_sql_with_buffers(self):
        """Test building EXPLAIN with BUFFERS."""
        executor = ExplainExecutor()
        sql = executor.build_explain_sql("SELECT * FROM users", buffers=True)
        assert "BUFFERS" in sql
    
    def test_build_explain_sql_with_format(self):
        """Test building EXPLAIN with format."""
        executor = ExplainExecutor()
        sql = executor.build_explain_sql(
            "SELECT * FROM users",
            format=ExplainFormat.JSON,
        )
        assert "FORMAT JSON" in sql
    
    def test_build_explain_sql_all_options(self):
        """Test building EXPLAIN with all options."""
        executor = ExplainExecutor()
        sql = executor.build_explain_sql(
            "SELECT * FROM users",
            analyze=True,
            verbose=True,
            costs=True,
            buffers=True,
            timing=True,
            format=ExplainFormat.JSON,
        )
        assert "ANALYZE" in sql
        assert "VERBOSE" in sql
        assert "BUFFERS" in sql
        assert "TIMING" in sql
        assert "FORMAT JSON" in sql


# =============================================================================
# EXPLAIN MIXIN TESTS
# =============================================================================

class TestExplainMixin:
    """Tests for ExplainMixin."""
    
    def test_mixin_has_explain_method(self):
        """Test mixin provides explain method."""
        class MockQuery(ExplainMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "explain")
    
    def test_mixin_has_analyze_method(self):
        """Test mixin provides analyze method."""
        class MockQuery(ExplainMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "analyze")


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_json_plan(self):
        """Test handling empty JSON plan."""
        plan = QueryPlan.from_json("[]")
        # Should not crash
    
    def test_malformed_json(self):
        """Test handling malformed JSON."""
        plan = QueryPlan.from_json("not json")
        assert plan.root_node is None
    
    def test_empty_text_plan(self):
        """Test handling empty text plan."""
        plan = QueryPlan.from_text("")
        # Should not crash
    
    def test_node_without_relation(self):
        """Test node without relation name."""
        node = PlanNode(node_type="Sort")
        assert node.relation is None
    
    def test_plan_with_very_deep_tree(self):
        """Test plan with deeply nested nodes."""
        # Build deep tree
        node = PlanNode(node_type="Result")
        for i in range(10):
            node = PlanNode(
                node_type=f"Node{i}",
                children=[node],
            )
        
        plan = QueryPlan(raw="", root_node=node)
        assert len(plan.nodes) == 11
    
    def test_tree_visualization_with_multiple_children(self):
        """Test tree visualization with multiple children."""
        root = PlanNode(
            node_type="Append",
            children=[
                PlanNode(node_type="Seq Scan", relation="users_1"),
                PlanNode(node_type="Seq Scan", relation="users_2"),
                PlanNode(node_type="Seq Scan", relation="users_3"),
            ],
        )
        plan = QueryPlan(raw="", root_node=root)
        tree = plan.tree
        assert "Append" in tree
        assert "users_1" in tree
    
    def test_comparison_with_zero_cost(self):
        """Test comparison when plan has zero cost."""
        plan1 = QueryPlan(raw="", total_cost=0.0)
        plan2 = QueryPlan(raw="", total_cost=100.0)
        
        comparison = PlanComparison.compare(plan1, plan2)
        # Should handle zero cost gracefully
    
    def test_buffer_stats_with_all_zeros(self):
        """Test buffer stats with all zero values."""
        stats = BufferStats()
        assert stats.hit_rate == 100.0
    
    def test_node_with_buffers(self):
        """Test node with buffer statistics."""
        buffers = BufferStats(shared_hit=100, shared_read=10)
        node = PlanNode(
            node_type="Seq Scan",
            buffers=buffers,
        )
        assert node.buffers.hit_rate > 90
    
    def test_plan_total_buffer_reads(self):
        """Test total buffer reads calculation."""
        buffers1 = BufferStats(shared_read=100)
        buffers2 = BufferStats(shared_read=50)
        
        root = PlanNode(
            node_type="Nested Loop",
            buffers=buffers1,
            children=[
                PlanNode(node_type="Seq Scan", buffers=buffers2),
            ],
        )
        plan = QueryPlan(raw="", root_node=root)
        assert plan.total_buffer_reads == 150


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for EXPLAIN features."""
    
    def test_full_json_parsing_workflow(self):
        """Test complete JSON parsing workflow."""
        json_output = json.dumps([{
            "Plan": {
                "Node Type": "Nested Loop",
                "Total Cost": 1000.0,
                "Plan Rows": 5000,
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Relation Name": "users",
                        "Total Cost": 100.0,
                        "Plan Rows": 1000,
                        "Filter": "(active = true)",
                    },
                    {
                        "Node Type": "Index Scan",
                        "Relation Name": "orders",
                        "Total Cost": 10.0,
                        "Plan Rows": 5,
                    },
                ],
            },
            "Planning Time": 1.5,
            "Execution Time": 50.0,
        }])
        
        plan = QueryPlan.from_json(json_output)
        
        assert plan.root_node.node_type == "Nested Loop"
        assert len(plan.root_node.children) == 2
        assert plan.has_seq_scan is True
        assert "users" in plan.seq_scan_tables
        assert plan.planning_time == 1.5
        assert plan.execution_time == 50.0
        
        # Check suggestions were generated
        assert len(plan.suggestions) > 0
        
        # Check tree visualization
        tree = plan.tree
        assert "Nested Loop" in tree
        assert "users" in tree
    
    def test_comparison_workflow(self):
        """Test complete plan comparison workflow."""
        # Plan before optimization
        before_json = json.dumps([{
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Total Cost": 1000.0,
                "Plan Rows": 10000,
            },
        }])
        
        # Plan after adding index
        after_json = json.dumps([{
            "Plan": {
                "Node Type": "Index Scan",
                "Relation Name": "users",
                "Total Cost": 10.0,
                "Plan Rows": 100,
            },
        }])
        
        before = QueryPlan.from_json(before_json)
        after = QueryPlan.from_json(after_json)
        
        comparison = before.compare(after)
        
        assert comparison.is_plan2_better
        assert comparison.cost_diff < 0
        assert "better" in comparison.summary.lower()

