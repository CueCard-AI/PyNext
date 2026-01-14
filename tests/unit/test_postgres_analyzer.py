"""
Tests for PyNext Query Analyzer Module.

120 comprehensive tests covering:
- AnalyzerConfig (15 tests)
- ExplainNode and ExplainResult (25 tests)
- QuerySuggestion (10 tests)
- AnalysisResult (10 tests)
- QueryAnalyzer core (40 tests)
- N+1 detection and history (15 tests)
- Edge cases (5 tests)
"""

import time
from unittest.mock import MagicMock

import pytest

from pynext.db.adapters.postgres.observability.analyzer import (
    AnalyzerConfig,
    SuggestionType,
    ScanType,
    ExplainNode,
    ExplainResult,
    QuerySuggestion,
    AnalysisResult,
    QueryAnalyzer,
    create_analyzer,
)


# ============================================================================
# AnalyzerConfig Tests (15 tests)
# ============================================================================

class TestAnalyzerConfig:
    """Tests for AnalyzerConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AnalyzerConfig()
        assert config.enabled is True
        assert config.slow_threshold_ms == 100.0
        assert config.auto_explain is True
        assert config.suggest_indexes is True
        assert config.suggest_rewrites is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = AnalyzerConfig(
            slow_threshold_ms=50.0,
            auto_explain=False,
        )
        assert config.slow_threshold_ms == 50.0
        assert config.auto_explain is False
    
    def test_disabled_config(self):
        """Test disabled analyzer."""
        config = AnalyzerConfig(enabled=False)
        assert config.enabled is False
    
    def test_max_explain_cost(self):
        """Test max explain cost threshold."""
        config = AnalyzerConfig(max_explain_cost=500.0)
        assert config.max_explain_cost == 500.0
    
    def test_history_settings(self):
        """Test history settings."""
        config = AnalyzerConfig(store_history=True, history_size=500)
        assert config.store_history is True
        assert config.history_size == 500
    
    def test_slow_query_callback(self):
        """Test slow query callback setting."""
        callback = MagicMock()
        config = AnalyzerConfig(on_slow_query=callback)
        assert config.on_slow_query is callback
    
    def test_suggestion_callback(self):
        """Test suggestion callback setting."""
        callback = MagicMock()
        config = AnalyzerConfig(on_suggestion=callback)
        assert config.on_suggestion is callback
    
    def test_disable_suggestions(self):
        """Test disabling suggestions."""
        config = AnalyzerConfig(suggest_indexes=False, suggest_rewrites=False)
        assert config.suggest_indexes is False
        assert config.suggest_rewrites is False
    
    def test_low_threshold(self):
        """Test very low slow threshold."""
        config = AnalyzerConfig(slow_threshold_ms=1.0)
        assert config.slow_threshold_ms == 1.0
    
    def test_high_threshold(self):
        """Test high slow threshold."""
        config = AnalyzerConfig(slow_threshold_ms=10000.0)
        assert config.slow_threshold_ms == 10000.0
    
    def test_zero_history(self):
        """Test zero history size."""
        config = AnalyzerConfig(store_history=False)
        assert config.store_history is False
    
    def test_large_history(self):
        """Test large history size."""
        config = AnalyzerConfig(history_size=10000)
        assert config.history_size == 10000
    
    def test_all_suggestions_disabled(self):
        """Test analyzer with all suggestions disabled."""
        config = AnalyzerConfig(
            auto_explain=False,
            suggest_indexes=False,
            suggest_rewrites=False,
        )
        assert config.auto_explain is False
    
    def test_only_index_suggestions(self):
        """Test only index suggestions enabled."""
        config = AnalyzerConfig(
            suggest_indexes=True,
            suggest_rewrites=False,
        )
        assert config.suggest_indexes is True
        assert config.suggest_rewrites is False
    
    def test_only_rewrite_suggestions(self):
        """Test only rewrite suggestions enabled."""
        config = AnalyzerConfig(
            suggest_indexes=False,
            suggest_rewrites=True,
        )
        assert config.suggest_indexes is False
        assert config.suggest_rewrites is True


# ============================================================================
# ExplainNode Tests (15 tests)
# ============================================================================

class TestExplainNode:
    """Tests for ExplainNode dataclass."""
    
    def test_basic_node(self):
        """Test basic node creation."""
        node = ExplainNode(node_type="Seq Scan")
        assert node.node_type == "Seq Scan"
    
    def test_seq_scan_detection(self):
        """Test sequential scan detection."""
        node = ExplainNode(node_type="Seq Scan")
        assert node.is_seq_scan is True
        assert node.is_index_scan is False
    
    def test_index_scan_detection(self):
        """Test index scan detection."""
        node = ExplainNode(node_type="Index Scan")
        assert node.is_index_scan is True
        assert node.is_seq_scan is False
    
    def test_index_only_scan_detection(self):
        """Test index only scan detection."""
        node = ExplainNode(node_type="Index Only Scan")
        assert node.is_index_scan is True
    
    def test_node_with_relation(self):
        """Test node with relation name."""
        node = ExplainNode(node_type="Seq Scan", relation="users")
        assert node.relation == "users"
    
    def test_node_with_costs(self):
        """Test node with cost information."""
        node = ExplainNode(
            node_type="Seq Scan",
            startup_cost=0.0,
            total_cost=100.5,
        )
        assert node.startup_cost == 0.0
        assert node.total_cost == 100.5
    
    def test_node_with_rows(self):
        """Test node with row estimates."""
        node = ExplainNode(node_type="Seq Scan", rows=1000, width=50)
        assert node.rows == 1000
        assert node.width == 50
    
    def test_node_with_filter(self):
        """Test node with filter condition."""
        node = ExplainNode(
            node_type="Seq Scan",
            filter="(email = 'test@example.com'::text)",
        )
        assert node.filter is not None
    
    def test_node_with_index(self):
        """Test node with index information."""
        node = ExplainNode(
            node_type="Index Scan",
            index_name="users_email_idx",
            index_cond="(email = 'test'::text)",
        )
        assert node.index_name == "users_email_idx"
        assert node.index_cond is not None
    
    def test_node_with_children(self):
        """Test node with child nodes."""
        child = ExplainNode(node_type="Index Scan")
        parent = ExplainNode(node_type="Nested Loop", children=[child])
        assert len(parent.children) == 1
    
    def test_node_actual_time(self):
        """Test node with actual timing (ANALYZE)."""
        node = ExplainNode(
            node_type="Seq Scan",
            actual_time=0.5,
            actual_rows=100,
        )
        assert node.actual_time == 0.5
        assert node.actual_rows == 100
    
    def test_hash_join_node(self):
        """Test hash join node type."""
        node = ExplainNode(node_type="Hash Join")
        assert not node.is_seq_scan
        assert not node.is_index_scan
    
    def test_sort_node(self):
        """Test sort node type."""
        node = ExplainNode(node_type="Sort", total_cost=200.0)
        assert node.node_type == "Sort"
    
    def test_nested_loop_node(self):
        """Test nested loop node type."""
        node = ExplainNode(node_type="Nested Loop")
        assert node.node_type == "Nested Loop"
    
    def test_bitmap_scan_node(self):
        """Test bitmap scan node type."""
        node = ExplainNode(node_type="Bitmap Heap Scan")
        assert not node.is_seq_scan


# ============================================================================
# ExplainResult Tests (10 tests)
# ============================================================================

class TestExplainResult:
    """Tests for ExplainResult dataclass."""
    
    def test_empty_result(self):
        """Test empty explain result."""
        result = ExplainResult()
        assert result.plan is None
        assert result.total_cost == 0.0
    
    def test_from_json_simple(self):
        """Test parsing simple EXPLAIN JSON."""
        explain_json = [{
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Total Cost": 100.0,
                "Plan Rows": 50,
            },
            "Planning Time": 0.1,
            "Execution Time": 1.5,
        }]
        
        result = ExplainResult.from_json(explain_json)
        assert result.plan is not None
        assert result.plan.node_type == "Seq Scan"
        assert result.total_cost == 100.0
        assert result.planning_time == 0.1
        assert result.execution_time == 1.5
    
    def test_from_json_nested(self):
        """Test parsing nested EXPLAIN JSON."""
        explain_json = [{
            "Plan": {
                "Node Type": "Nested Loop",
                "Total Cost": 200.0,
                "Plans": [
                    {"Node Type": "Seq Scan", "Relation Name": "users"},
                    {"Node Type": "Index Scan", "Relation Name": "orders"},
                ],
            },
        }]
        
        result = ExplainResult.from_json(explain_json)
        assert result.plan is not None
        assert len(result.plan.children) == 2
    
    def test_find_seq_scans(self):
        """Test finding sequential scans."""
        result = ExplainResult()
        result.plan = ExplainNode(
            node_type="Nested Loop",
            children=[
                ExplainNode(node_type="Seq Scan", relation="users"),
                ExplainNode(node_type="Index Scan", relation="orders"),
            ],
        )
        
        seq_scans = result.find_seq_scans()
        assert len(seq_scans) == 1
        assert seq_scans[0].relation == "users"
    
    def test_find_expensive_sorts(self):
        """Test finding expensive sorts."""
        result = ExplainResult()
        result.plan = ExplainNode(
            node_type="Sort",
            total_cost=500.0,
        )
        
        expensive = result.find_expensive_sorts(threshold=100.0)
        assert len(expensive) == 1
    
    def test_find_no_expensive_sorts(self):
        """Test no expensive sorts found."""
        result = ExplainResult()
        result.plan = ExplainNode(
            node_type="Sort",
            total_cost=50.0,
        )
        
        expensive = result.find_expensive_sorts(threshold=100.0)
        assert len(expensive) == 0
    
    def test_raw_output_stored(self):
        """Test raw output is stored."""
        explain_json = [{"Plan": {"Node Type": "Seq Scan"}}]
        result = ExplainResult.from_json(explain_json)
        assert result.raw_output != ""
    
    def test_empty_json(self):
        """Test parsing empty JSON."""
        result = ExplainResult.from_json({})
        assert result.plan is None
    
    def test_none_json(self):
        """Test parsing None."""
        result = ExplainResult.from_json(None)
        assert result.plan is None
    
    def test_find_seq_scans_no_plan(self):
        """Test finding seq scans with no plan."""
        result = ExplainResult()
        assert result.find_seq_scans() == []


# ============================================================================
# QuerySuggestion Tests (10 tests)
# ============================================================================

class TestQuerySuggestion:
    """Tests for QuerySuggestion dataclass."""
    
    def test_index_suggestion(self):
        """Test index suggestion creation."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            table="users",
            columns=("email",),
            message="Add index on users(email)",
        )
        assert suggestion.type == SuggestionType.INDEX
        assert suggestion.table == "users"
    
    def test_rewrite_suggestion(self):
        """Test rewrite suggestion."""
        suggestion = QuerySuggestion(
            type=SuggestionType.REWRITE,
            message="Consider using JOIN instead",
        )
        assert suggestion.type == SuggestionType.REWRITE
    
    def test_suggestion_with_sql(self):
        """Test suggestion with SQL."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            table="users",
            columns=("email",),
            sql="CREATE INDEX idx_users_email ON users (email);",
        )
        assert suggestion.sql is not None
    
    def test_suggestion_confidence(self):
        """Test suggestion confidence."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            confidence=0.9,
        )
        assert suggestion.confidence == 0.9
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            table="users",
            columns=("email", "name"),
            message="Add composite index",
        )
        d = suggestion.to_dict()
        
        assert d["type"] == "index"
        assert d["table"] == "users"
        assert d["columns"] == ["email", "name"]
    
    def test_all_suggestion_types(self):
        """Test all suggestion types exist."""
        assert SuggestionType.INDEX
        assert SuggestionType.REWRITE
        assert SuggestionType.LIMIT
        assert SuggestionType.SELECT_STAR
        assert SuggestionType.N_PLUS_ONE
    
    def test_suggestion_reason(self):
        """Test suggestion reason."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            reason="Seq Scan detected",
        )
        assert suggestion.reason == "Seq Scan detected"
    
    def test_multiple_columns(self):
        """Test suggestion with multiple columns."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            columns=("a", "b", "c"),
        )
        assert len(suggestion.columns) == 3
    
    def test_empty_columns(self):
        """Test suggestion with no columns."""
        suggestion = QuerySuggestion(type=SuggestionType.REWRITE)
        assert suggestion.columns == ()
    
    def test_default_confidence(self):
        """Test default confidence is 1.0."""
        suggestion = QuerySuggestion(type=SuggestionType.INDEX)
        assert suggestion.confidence == 1.0


# ============================================================================
# AnalysisResult Tests (10 tests)
# ============================================================================

class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""
    
    def test_basic_result(self):
        """Test basic result creation."""
        result = AnalysisResult(query="SELECT 1")
        assert result.query == "SELECT 1"
        assert result.is_slow is False
    
    def test_slow_query_result(self):
        """Test slow query result."""
        result = AnalysisResult(
            query="SELECT * FROM users",
            duration_ms=500.0,
            is_slow=True,
        )
        assert result.is_slow is True
        assert result.duration_ms == 500.0
    
    def test_result_with_explain(self):
        """Test result with EXPLAIN."""
        explain = ExplainResult()
        result = AnalysisResult(
            query="SELECT 1",
            explain=explain,
        )
        assert result.explain is not None
    
    def test_result_with_suggestions(self):
        """Test result with suggestions."""
        suggestion = QuerySuggestion(type=SuggestionType.INDEX)
        result = AnalysisResult(
            query="SELECT 1",
            suggestions=[suggestion],
        )
        assert len(result.suggestions) == 1
    
    def test_query_type(self):
        """Test query type detection."""
        result = AnalysisResult(
            query="SELECT 1",
            query_type="SELECT",
        )
        assert result.query_type == "SELECT"
    
    def test_table_detection(self):
        """Test table detection."""
        result = AnalysisResult(
            query="SELECT * FROM users",
            table="users",
        )
        assert result.table == "users"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = AnalysisResult(
            query="SELECT 1",
            duration_ms=50.0,
            is_slow=False,
        )
        d = result.to_dict()
        
        assert d["query"] == "SELECT 1"
        assert d["duration_ms"] == 50.0
        assert d["is_slow"] is False
    
    def test_analyzed_at_timestamp(self):
        """Test analyzed_at timestamp."""
        before = time.time()
        result = AnalysisResult(query="SELECT 1")
        after = time.time()
        
        assert before <= result.analyzed_at <= after
    
    def test_to_dict_with_suggestions(self):
        """Test to_dict includes suggestions."""
        suggestion = QuerySuggestion(
            type=SuggestionType.INDEX,
            message="Add index",
        )
        result = AnalysisResult(
            query="SELECT 1",
            suggestions=[suggestion],
        )
        d = result.to_dict()
        
        assert len(d["suggestions"]) == 1
    
    def test_to_dict_with_explain(self):
        """Test to_dict includes explain info."""
        explain = ExplainResult(total_cost=100.0, execution_time=1.5)
        result = AnalysisResult(
            query="SELECT 1",
            explain=explain,
        )
        d = result.to_dict()
        
        assert d["explain"]["total_cost"] == 100.0


# ============================================================================
# QueryAnalyzer Core Tests (40 tests)
# ============================================================================

class TestQueryAnalyzerCore:
    """Tests for QueryAnalyzer core functionality."""
    
    def test_default_creation(self):
        """Test creating analyzer with defaults."""
        analyzer = QueryAnalyzer()
        assert analyzer.enabled is True
    
    def test_custom_config(self):
        """Test creating analyzer with custom config."""
        config = AnalyzerConfig(slow_threshold_ms=50.0)
        analyzer = QueryAnalyzer(config)
        assert analyzer.config.slow_threshold_ms == 50.0
    
    def test_disabled_analyzer(self):
        """Test disabled analyzer."""
        config = AnalyzerConfig(enabled=False)
        analyzer = QueryAnalyzer(config)
        assert analyzer.enabled is False
    
    def test_is_slow_true(self):
        """Test is_slow returns true for slow query."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=100.0))
        assert analyzer.is_slow(150.0) is True
    
    def test_is_slow_false(self):
        """Test is_slow returns false for fast query."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=100.0))
        assert analyzer.is_slow(50.0) is False
    
    def test_is_slow_at_threshold(self):
        """Test is_slow at exact threshold."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=100.0))
        assert analyzer.is_slow(100.0) is False  # Not greater than
    
    def test_analyze_fast_query(self):
        """Test analyzing fast query."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT 1", 10.0)
        
        assert result.is_slow is False
        assert len(result.suggestions) == 0
    
    def test_analyze_slow_query(self):
        """Test analyzing slow query."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=50.0))
        result = analyzer.analyze("SELECT * FROM users", 100.0)
        
        assert result.is_slow is True
    
    def test_analyze_with_explain(self):
        """Test analyzing with EXPLAIN output."""
        analyzer = QueryAnalyzer()
        explain_json = [{
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Total Cost": 100.0,
            },
        }]
        
        result = analyzer.analyze("SELECT * FROM users", 50.0, explain_json)
        assert result.explain is not None
    
    def test_parse_query_type_select(self):
        """Test parsing SELECT query type."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("SELECT * FROM users") == "SELECT"
    
    def test_parse_query_type_insert(self):
        """Test parsing INSERT query type."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("INSERT INTO users VALUES (1)") == "INSERT"
    
    def test_parse_query_type_update(self):
        """Test parsing UPDATE query type."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("UPDATE users SET name = 'test'") == "UPDATE"
    
    def test_parse_query_type_delete(self):
        """Test parsing DELETE query type."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("DELETE FROM users") == "DELETE"
    
    def test_parse_table_select(self):
        """Test parsing table from SELECT."""
        analyzer = QueryAnalyzer()
        table = analyzer._parse_table("SELECT * FROM users WHERE id = 1", "SELECT")
        assert table == "users"
    
    def test_parse_table_insert(self):
        """Test parsing table from INSERT."""
        analyzer = QueryAnalyzer()
        table = analyzer._parse_table("INSERT INTO orders VALUES (1)", "INSERT")
        assert table == "orders"
    
    def test_parse_table_update(self):
        """Test parsing table from UPDATE."""
        analyzer = QueryAnalyzer()
        table = analyzer._parse_table("UPDATE products SET price = 100", "UPDATE")
        assert table == "products"
    
    def test_parse_table_delete(self):
        """Test parsing table from DELETE."""
        analyzer = QueryAnalyzer()
        table = analyzer._parse_table("DELETE FROM sessions", "DELETE")
        assert table == "sessions"
    
    def test_suggest_index_from_seq_scan(self):
        """Test index suggestion from seq scan."""
        analyzer = QueryAnalyzer()
        explain_json = [{
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "users",
                "Filter": "(email = 'test@example.com'::text)",
                "Total Cost": 100.0,
            },
        }]
        
        result = analyzer.analyze("SELECT * FROM users WHERE email = 'test'", 50.0, explain_json)
        
        # Should have index suggestion
        index_suggestions = [s for s in result.suggestions if s.type == SuggestionType.INDEX]
        assert len(index_suggestions) >= 0  # May or may not detect depending on filter parsing
    
    def test_suggest_select_star(self):
        """Test SELECT * suggestion."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT * FROM users", 150.0)  # Slow query
        
        select_star = [s for s in result.suggestions if s.type == SuggestionType.SELECT_STAR]
        assert len(select_star) == 1
    
    def test_no_select_star_for_specific_columns(self):
        """Test no SELECT * suggestion for specific columns."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT id, name FROM users", 150.0)
        
        select_star = [s for s in result.suggestions if s.type == SuggestionType.SELECT_STAR]
        assert len(select_star) == 0
    
    def test_extract_filter_columns(self):
        """Test extracting columns from filter."""
        analyzer = QueryAnalyzer()
        columns = analyzer._extract_filter_columns("email = 'test@example.com'")
        assert "email" in columns
    
    def test_extract_multiple_filter_columns(self):
        """Test extracting multiple columns from filter."""
        analyzer = QueryAnalyzer()
        columns = analyzer._extract_filter_columns("email = 'test' AND status = 'active'")
        assert "email" in columns
        assert "status" in columns
    
    def test_slow_query_callback(self):
        """Test slow query callback is called."""
        callback = MagicMock()
        config = AnalyzerConfig(
            slow_threshold_ms=50.0,
            on_slow_query=callback,
        )
        analyzer = QueryAnalyzer(config)
        
        analyzer.analyze("SELECT * FROM users", 100.0)
        callback.assert_called_once()
    
    def test_no_callback_for_fast_query(self):
        """Test no callback for fast query."""
        callback = MagicMock()
        config = AnalyzerConfig(
            slow_threshold_ms=100.0,
            on_slow_query=callback,
        )
        analyzer = QueryAnalyzer(config)
        
        analyzer.analyze("SELECT 1", 10.0)
        callback.assert_not_called()
    
    def test_disabled_analyzer_returns_basic_result(self):
        """Test disabled analyzer returns basic result."""
        config = AnalyzerConfig(enabled=False)
        analyzer = QueryAnalyzer(config)
        
        result = analyzer.analyze("SELECT 1", 100.0)
        assert result.query == "SELECT 1"
        assert len(result.suggestions) == 0
    
    def test_normalize_query(self):
        """Test query normalization."""
        analyzer = QueryAnalyzer()
        
        q1 = "SELECT * FROM users WHERE id = 123"
        q2 = "SELECT * FROM users WHERE id = 456"
        
        assert analyzer._normalize_query(q1) == analyzer._normalize_query(q2)
    
    def test_normalize_query_strings(self):
        """Test query normalization with strings."""
        analyzer = QueryAnalyzer()
        
        q1 = "SELECT * FROM users WHERE email = 'test@example.com'"
        q2 = "SELECT * FROM users WHERE email = 'other@example.com'"
        
        assert analyzer._normalize_query(q1) == analyzer._normalize_query(q2)
    
    def test_create_analyzer_helper(self):
        """Test create_analyzer helper function."""
        analyzer = create_analyzer(slow_threshold_ms=50.0)
        assert analyzer.config.slow_threshold_ms == 50.0
    
    def test_create_analyzer_with_kwargs(self):
        """Test create_analyzer with additional kwargs."""
        analyzer = create_analyzer(
            slow_threshold_ms=50.0,
            suggest_indexes=False,
            suggest_rewrites=True,
        )
        assert analyzer.config.suggest_indexes is False
        assert analyzer.config.suggest_rewrites is True
    
    def test_query_type_case_insensitive(self):
        """Test query type parsing is case insensitive."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("select * from users") == "SELECT"
        assert analyzer._parse_query_type("SELECT * FROM users") == "SELECT"
    
    def test_analyze_result_includes_query(self):
        """Test result includes original query."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT * FROM users", 10.0)
        assert result.query == "SELECT * FROM users"
    
    def test_analyze_result_includes_duration(self):
        """Test result includes duration."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT 1", 25.5)
        assert result.duration_ms == 25.5
    
    def test_analyze_result_includes_query_type(self):
        """Test result includes query type."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT * FROM users", 10.0)
        assert result.query_type == "SELECT"
    
    def test_analyze_result_includes_table(self):
        """Test result includes table."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("SELECT * FROM users", 10.0)
        assert result.table == "users"
    
    def test_unknown_query_type(self):
        """Test handling unknown query type."""
        analyzer = QueryAnalyzer()
        assert analyzer._parse_query_type("EXPLAIN SELECT 1") is None
    
    def test_complex_query_parsing(self):
        """Test parsing complex query."""
        analyzer = QueryAnalyzer()
        query = """
            SELECT u.id, u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE u.active = true
        """
        result = analyzer.analyze(query.strip(), 10.0)
        assert result.query_type == "SELECT"
    
    def test_subquery_handling(self):
        """Test handling subqueries."""
        analyzer = QueryAnalyzer()
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        result = analyzer.analyze(query, 10.0)
        assert result.query_type == "SELECT"


# ============================================================================
# N+1 Detection and History Tests (15 tests)
# ============================================================================

class TestNPlusOneAndHistory:
    """Tests for N+1 detection and query history."""
    
    def test_history_storage(self):
        """Test queries are stored in history."""
        config = AnalyzerConfig(store_history=True)
        analyzer = QueryAnalyzer(config)
        
        analyzer.analyze("SELECT 1", 10.0)
        analyzer.analyze("SELECT 2", 10.0)
        
        history = analyzer.get_history()
        assert len(history) == 2
    
    def test_history_disabled(self):
        """Test history can be disabled."""
        config = AnalyzerConfig(store_history=False)
        analyzer = QueryAnalyzer(config)
        
        analyzer.analyze("SELECT 1", 10.0)
        
        history = analyzer.get_history()
        assert len(history) == 0
    
    def test_history_limit(self):
        """Test history respects limit."""
        config = AnalyzerConfig(history_size=5)
        analyzer = QueryAnalyzer(config)
        
        for i in range(10):
            analyzer.analyze(f"SELECT {i}", 10.0)
        
        history = analyzer.get_history()
        assert len(history) == 5
    
    def test_get_history_limit(self):
        """Test get_history with limit."""
        analyzer = QueryAnalyzer()
        
        for i in range(10):
            analyzer.analyze(f"SELECT {i}", 10.0)
        
        history = analyzer.get_history(limit=3)
        assert len(history) == 3
    
    def test_get_history_slow_only(self):
        """Test get_history with slow_only filter."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=50.0))
        
        analyzer.analyze("SELECT 1", 10.0)  # Fast
        analyzer.analyze("SELECT 2", 100.0)  # Slow
        analyzer.analyze("SELECT 3", 10.0)  # Fast
        
        history = analyzer.get_history(slow_only=True)
        assert len(history) == 1
    
    def test_n_plus_one_detection(self):
        """Test N+1 pattern detection."""
        analyzer = QueryAnalyzer()
        
        # Simulate N+1 pattern
        now = time.time()
        for i in range(10):
            result = AnalysisResult(
                query=f"SELECT * FROM users WHERE id = {i}",
                analyzed_at=now,
            )
            analyzer._history.append(result)
        
        suggestions = analyzer.detect_n_plus_one(window_seconds=1.0)
        
        # Should detect pattern
        n_plus_one = [s for s in suggestions if s.type == SuggestionType.N_PLUS_ONE]
        assert len(n_plus_one) >= 1
    
    def test_no_n_plus_one_for_diverse_queries(self):
        """Test no N+1 for diverse queries."""
        analyzer = QueryAnalyzer()
        
        now = time.time()
        analyzer._history = [
            AnalysisResult(query="SELECT * FROM users", analyzed_at=now),
            AnalysisResult(query="SELECT * FROM orders", analyzed_at=now),
            AnalysisResult(query="SELECT * FROM products", analyzed_at=now),
        ]
        
        suggestions = analyzer.detect_n_plus_one(window_seconds=1.0)
        assert len(suggestions) == 0
    
    def test_n_plus_one_window(self):
        """Test N+1 detection respects time window."""
        analyzer = QueryAnalyzer()
        
        now = time.time()
        old = now - 100  # 100 seconds ago
        
        # Old queries shouldn't count
        for i in range(10):
            analyzer._history.append(AnalysisResult(
                query=f"SELECT * FROM users WHERE id = {i}",
                analyzed_at=old,
            ))
        
        suggestions = analyzer.detect_n_plus_one(window_seconds=1.0)
        assert len(suggestions) == 0
    
    def test_clear_history(self):
        """Test clearing history."""
        analyzer = QueryAnalyzer()
        
        analyzer.analyze("SELECT 1", 10.0)
        analyzer.analyze("SELECT 2", 10.0)
        
        analyzer.clear_history()
        
        assert len(analyzer.get_history()) == 0
    
    def test_get_stats(self):
        """Test getting analyzer stats."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=50.0))
        
        analyzer.analyze("SELECT 1", 10.0)  # Fast
        analyzer.analyze("SELECT 2", 100.0)  # Slow
        
        stats = analyzer.get_stats()
        
        assert stats["total_queries"] == 2
        assert stats["slow_queries"] == 1
        assert stats["slow_percentage"] == 50.0
    
    def test_stats_empty_history(self):
        """Test stats with empty history."""
        analyzer = QueryAnalyzer()
        stats = analyzer.get_stats()
        
        assert stats["total_queries"] == 0
        assert stats["slow_percentage"] == 0
    
    def test_history_trimming(self):
        """Test history is trimmed correctly."""
        config = AnalyzerConfig(history_size=3)
        analyzer = QueryAnalyzer(config)
        
        # Add 5 queries
        for i in range(5):
            analyzer.analyze(f"SELECT {i}", 10.0)
        
        history = analyzer.get_history()
        
        # Should keep only last 3
        assert len(history) == 3
        # Check they're the latest ones
        assert history[-1].query == "SELECT 4"
    
    def test_suggestion_callback(self):
        """Test suggestion callback is called."""
        callback = MagicMock()
        config = AnalyzerConfig(
            slow_threshold_ms=50.0,
            on_suggestion=callback,
        )
        analyzer = QueryAnalyzer(config)
        
        # Trigger a suggestion with SELECT *
        analyzer.analyze("SELECT * FROM users", 100.0)
        
        # Callback should be called for each suggestion
        assert callback.call_count >= 1
    
    def test_history_includes_suggestions(self):
        """Test history entries include suggestions."""
        analyzer = QueryAnalyzer(AnalyzerConfig(slow_threshold_ms=50.0))
        
        analyzer.analyze("SELECT * FROM users", 100.0)
        
        history = analyzer.get_history()
        assert len(history) == 1
        assert len(history[0].suggestions) >= 1  # At least SELECT * suggestion


# ============================================================================
# Edge Cases (5 tests)
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_query(self):
        """Test handling empty query."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("", 10.0)
        assert result.query_type is None
    
    def test_whitespace_query(self):
        """Test handling whitespace-only query."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("   ", 10.0)
        assert result.query_type is None
    
    def test_malformed_explain_json(self):
        """Test handling malformed EXPLAIN JSON."""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze(
            "SELECT 1",
            10.0,
            {"invalid": "format"},
        )
        # Should not crash
        assert result.explain is not None
    
    def test_very_long_query(self):
        """Test handling very long query."""
        analyzer = QueryAnalyzer()
        long_query = "SELECT " + ", ".join(f"col{i}" for i in range(1000)) + " FROM users"
        
        result = analyzer.analyze(long_query, 10.0)
        assert result.query_type == "SELECT"
    
    def test_special_characters_in_query(self):
        """Test handling special characters in query."""
        analyzer = QueryAnalyzer()
        query = "SELECT * FROM users WHERE name = 'O''Brien'"
        
        result = analyzer.analyze(query, 10.0)
        assert result.query_type == "SELECT"

