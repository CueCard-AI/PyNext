"""
Tests for Layer Loading - Usage Tracking and Manifest Generation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests the UsageTracker system that determines which runtime layers are needed:
1. Feature recording during transpilation
2. Manifest generation with layer classification
3. Layer boundary correctness
4. Size estimation

=============================================================================
LAYERS TESTED
=============================================================================

Layer 0: at, slice, bool, eq, mod, floordiv, range, len
Layer 1: str.*, list.*, dict.*, set.* methods
Layer 2: errors, dunders, generators
Layer 3: stdlib modules (json, math, re, random)

=============================================================================
WHY THESE TESTS EXIST
=============================================================================

Correct layer classification is critical for bundle optimization.
Wrong classification leads to:
- Layer 0 bloat (too many features marked essential)
- Missing features (features not loaded when needed)
- Inefficient bundling (wrong layer boundaries)
"""

import pytest
from pynext.transpiler._internal.usage_tracker import (
    UsageTracker, UsageManifest,
    LAYER_0_FEATURES, LAYER_1_FEATURES, LAYER_2_FEATURES,
    LAYER_1_STR_FEATURES, LAYER_1_LIST_FEATURES, LAYER_1_DICT_FEATURES,
    LAYER_2_ERROR_FEATURES, LAYER_2_DUNDER_FEATURES,
    STDLIB_MODULES,
    classify_feature, get_layer_size_estimate,
)


# =============================================================================
# USAGE TRACKER BASIC TESTS
# =============================================================================

class TestUsageTrackerBasic:
    """Basic UsageTracker functionality tests."""
    
    def test_record_single_feature(self):
        """Record a single feature."""
        tracker = UsageTracker()
        tracker.record("at")
        assert tracker.has("at")
    
    def test_record_multiple_features(self):
        """Record multiple features."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("bool")
        tracker.record("slice")
        assert tracker.has("at")
        assert tracker.has("bool")
        assert tracker.has("slice")
    
    def test_record_many(self):
        """Record features with record_many()."""
        tracker = UsageTracker()
        tracker.record_many(["at", "bool", "eq"])
        assert tracker.has("at")
        assert tracker.has("bool")
        assert tracker.has("eq")
    
    def test_has_missing_feature(self):
        """has() returns False for unrecorded features."""
        tracker = UsageTracker()
        tracker.record("at")
        assert not tracker.has("slice")
    
    def test_get_features(self):
        """get_features() returns all recorded features."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("bool")
        features = tracker.get_features()
        assert features == {"at", "bool"}
    
    def test_reset(self):
        """reset() clears all features."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("bool")
        tracker.reset()
        assert not tracker.has("at")
        assert not tracker.has("bool")
    
    def test_merge(self):
        """merge() combines features from another tracker."""
        tracker1 = UsageTracker()
        tracker1.record("at")
        
        tracker2 = UsageTracker()
        tracker2.record("bool")
        
        tracker1.merge(tracker2)
        assert tracker1.has("at")
        assert tracker1.has("bool")


# =============================================================================
# MANIFEST GENERATION TESTS
# =============================================================================

class TestManifestGeneration:
    """Tests for manifest generation."""
    
    def test_manifest_layer0_only(self):
        """Manifest with only Layer 0 features."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("bool")
        
        manifest = tracker.get_manifest()
        assert "at" in manifest.layer0
        assert "bool" in manifest.layer0
        assert manifest.layer1 == []
        assert manifest.layer2 == []
        assert manifest.stdlib == []
    
    def test_manifest_layer1_str(self):
        """Manifest with string methods."""
        tracker = UsageTracker()
        tracker.record("str.split")
        tracker.record("str.replace")
        
        manifest = tracker.get_manifest()
        assert "str.split" in manifest.layer1
        assert "str.replace" in manifest.layer1
    
    def test_manifest_layer2_errors(self):
        """Manifest with error types."""
        tracker = UsageTracker()
        tracker.record("ValueError")
        tracker.record("KeyError")
        
        manifest = tracker.get_manifest()
        assert "ValueError" in manifest.layer2
        assert "KeyError" in manifest.layer2
    
    def test_manifest_stdlib(self):
        """Manifest with stdlib modules."""
        tracker = UsageTracker()
        tracker.record("json")
        tracker.record("random")
        
        manifest = tracker.get_manifest()
        assert "json" in manifest.stdlib
        assert "random" in manifest.stdlib
    
    def test_manifest_mixed_layers(self):
        """Manifest with features from multiple layers."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("str.split")
        tracker.record("ValueError")
        tracker.record("json")
        
        manifest = tracker.get_manifest()
        assert "at" in manifest.layer0
        assert "str.split" in manifest.layer1
        assert "ValueError" in manifest.layer2
        assert "json" in manifest.stdlib
    
    def test_manifest_sorted(self):
        """Manifest features are sorted for determinism."""
        tracker = UsageTracker()
        tracker.record("slice")
        tracker.record("at")
        tracker.record("bool")
        
        manifest = tracker.get_manifest()
        assert manifest.layer0 == sorted(manifest.layer0)
    
    def test_manifest_to_dict(self):
        """Manifest can be converted to dict."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("str.split")
        
        manifest = tracker.get_manifest()
        d = manifest.to_dict()
        
        assert "layer0" in d
        assert "layer1" in d
        assert "layer2" in d
        assert "stdlib" in d
    
    def test_manifest_is_empty(self):
        """is_empty() returns True for empty manifest."""
        tracker = UsageTracker()
        manifest = tracker.get_manifest()
        assert manifest.is_empty()
        
        tracker.record("at")
        manifest = tracker.get_manifest()
        assert not manifest.is_empty()
    
    def test_manifest_total_features(self):
        """total_features() counts all features."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("str.split")
        tracker.record("ValueError")
        tracker.record("json")
        
        manifest = tracker.get_manifest()
        assert manifest.total_features() == 4


# =============================================================================
# LAYER CLASSIFICATION TESTS
# =============================================================================

class TestLayerClassification:
    """Tests for classify_feature()."""
    
    def test_classify_layer0(self):
        """Layer 0 features classified correctly."""
        for feature in ["at", "slice", "bool", "eq", "mod", "floordiv", "range", "len"]:
            if feature in LAYER_0_FEATURES:
                assert classify_feature(feature) == "layer0"
    
    def test_classify_layer1_str(self):
        """String methods classified as layer1."""
        for feature in ["str.split", "str.replace", "str.strip"]:
            if feature in LAYER_1_STR_FEATURES:
                assert classify_feature(feature) == "layer1"
    
    def test_classify_layer1_list(self):
        """List methods classified as layer1."""
        for feature in ["list.remove", "list.insert", "list.index"]:
            if feature in LAYER_1_LIST_FEATURES:
                assert classify_feature(feature) == "layer1"
    
    def test_classify_layer2_errors(self):
        """Error types classified as layer2."""
        for feature in ["ValueError", "KeyError", "IndexError"]:
            if feature in LAYER_2_ERROR_FEATURES:
                assert classify_feature(feature) == "layer2"
    
    def test_classify_layer2_dunders(self):
        """Dunder methods classified as layer2."""
        for feature in ["dunders.add", "dunders.eq"]:
            if feature in LAYER_2_DUNDER_FEATURES:
                assert classify_feature(feature) == "layer2"
    
    def test_classify_stdlib(self):
        """Stdlib modules classified as stdlib."""
        for feature in ["json", "math", "re", "random"]:
            if feature in STDLIB_MODULES:
                assert classify_feature(feature) == "stdlib"
    
    def test_classify_unknown(self):
        """Unknown features classified as unknown."""
        assert classify_feature("unknown_feature") == "unknown"


# =============================================================================
# SIZE ESTIMATION TESTS
# =============================================================================

class TestSizeEstimation:
    """Tests for get_layer_size_estimate()."""
    
    def test_empty_manifest_size(self):
        """Empty manifest has no size."""
        manifest = UsageManifest()
        size = get_layer_size_estimate(manifest)
        assert size == 0
    
    def test_layer0_base_size(self):
        """Layer 0 adds base size."""
        manifest = UsageManifest(layer0=["at"])
        size = get_layer_size_estimate(manifest)
        assert size >= 500  # Base Layer 0 size
    
    def test_layer1_incremental_size(self):
        """Layer 1 adds per-method size."""
        manifest = UsageManifest(layer1=["str.split", "str.replace"])
        size = get_layer_size_estimate(manifest)
        assert size >= 200  # ~100B per method
    
    def test_layer2_size(self):
        """Layer 2 adds per-feature size."""
        manifest = UsageManifest(layer2=["ValueError", "KeyError"])
        size = get_layer_size_estimate(manifest)
        assert size >= 400  # ~200B per feature
    
    def test_stdlib_size(self):
        """Stdlib adds per-module size."""
        manifest = UsageManifest(stdlib=["json", "random"])
        size = get_layer_size_estimate(manifest)
        assert size >= 1000  # ~500B per module
    
    def test_combined_size(self):
        """Combined layers add up."""
        manifest = UsageManifest(
            layer0=["at", "bool"],
            layer1=["str.split"],
            layer2=["ValueError"],
            stdlib=["json"]
        )
        size = get_layer_size_estimate(manifest)
        # Should be sum of all layers
        assert size >= 500 + 100 + 200 + 500


# =============================================================================
# LAYER DEFINITION TESTS
# =============================================================================

class TestLayerDefinitions:
    """Tests for layer feature set definitions."""
    
    def test_layer0_has_8_essentials(self):
        """Layer 0 contains the 8 essential functions."""
        essentials = {"at", "slice", "bool", "eq", "mod", "floordiv", "range", "len"}
        for feature in essentials:
            assert feature in LAYER_0_FEATURES, f"Missing {feature} in Layer 0"
    
    def test_layer1_str_has_common_methods(self):
        """Layer 1 str has common string methods."""
        common = {"str.split", "str.replace", "str.strip"}
        for feature in common:
            assert feature in LAYER_1_STR_FEATURES, f"Missing {feature}"
    
    def test_layer1_list_has_common_methods(self):
        """Layer 1 list has common list methods."""
        common = {"list.append", "list.pop", "list.remove"}
        for feature in common:
            assert feature in LAYER_1_LIST_FEATURES, f"Missing {feature}"
    
    def test_layer2_errors_has_common_exceptions(self):
        """Layer 2 has common exception types."""
        common = {"ValueError", "TypeError", "KeyError", "IndexError"}
        for feature in common:
            assert feature in LAYER_2_ERROR_FEATURES, f"Missing {feature}"
    
    def test_stdlib_has_common_modules(self):
        """Stdlib has common modules."""
        common = {"json", "math", "re", "random"}
        for feature in common:
            assert feature in STDLIB_MODULES, f"Missing {feature}"
    
    def test_no_overlap_layer0_layer1(self):
        """Layer 0 and Layer 1 don't overlap."""
        overlap = LAYER_0_FEATURES & LAYER_1_FEATURES
        assert len(overlap) == 0, f"Overlap: {overlap}"
    
    def test_no_overlap_layer1_layer2(self):
        """Layer 1 and Layer 2 don't overlap."""
        overlap = LAYER_1_FEATURES & LAYER_2_FEATURES
        assert len(overlap) == 0, f"Overlap: {overlap}"
    
    def test_no_overlap_layer2_stdlib(self):
        """Layer 2 and Stdlib don't overlap."""
        overlap = LAYER_2_FEATURES & STDLIB_MODULES
        assert len(overlap) == 0, f"Overlap: {overlap}"


# =============================================================================
# REAL-WORLD SCENARIO TESTS
# =============================================================================

class TestRealWorldScenarios:
    """Tests simulating real transpilation scenarios."""
    
    def test_minimal_app(self):
        """Minimal app uses only Layer 0."""
        tracker = UsageTracker()
        # items[-1]
        tracker.record("at")
        
        manifest = tracker.get_manifest()
        assert manifest.layer0 == ["at"]
        assert manifest.layer1 == []
        assert manifest.layer2 == []
        assert manifest.stdlib == []
    
    def test_string_processing_app(self):
        """String processing app uses Layer 0 + Layer 1."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("bool")
        tracker.record("str.split")
        tracker.record("str.strip")
        tracker.record("str.replace")
        
        manifest = tracker.get_manifest()
        assert len(manifest.layer0) >= 2
        assert len(manifest.layer1) >= 3
        assert manifest.layer2 == []
    
    def test_error_handling_app(self):
        """App with error handling uses Layer 2."""
        tracker = UsageTracker()
        tracker.record("at")
        tracker.record("ValueError")
        tracker.record("KeyError")
        
        manifest = tracker.get_manifest()
        assert "ValueError" in manifest.layer2
        assert "KeyError" in manifest.layer2
    
    def test_custom_operators_app(self):
        """App with custom operators uses Layer 2 dunders."""
        tracker = UsageTracker()
        tracker.record("dunders.add")
        tracker.record("dunders.eq")
        
        manifest = tracker.get_manifest()
        assert "dunders.add" in manifest.layer2
        assert "dunders.eq" in manifest.layer2
    
    def test_full_app(self):
        """Full app uses all layers."""
        tracker = UsageTracker()
        # Layer 0
        tracker.record("at")
        tracker.record("bool")
        tracker.record("len")
        # Layer 1
        tracker.record("str.split")
        tracker.record("list.append")
        tracker.record("dict.get")
        # Layer 2
        tracker.record("ValueError")
        tracker.record("dunders.add")
        # Stdlib
        tracker.record("json")
        tracker.record("random")
        
        manifest = tracker.get_manifest()
        assert len(manifest.layer0) >= 3
        assert len(manifest.layer1) >= 3
        assert len(manifest.layer2) >= 2
        assert len(manifest.stdlib) >= 2

