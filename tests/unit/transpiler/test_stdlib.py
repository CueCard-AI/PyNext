"""
Phase 18.4: Standard Library Transpiler Tests

Comprehensive tests for Python standard library transpilation.
Tests verify the emitter produces correct JavaScript for:
- json (loads, dumps)
- math (functions, constants)
- re (match, search, sub, findall, split)
- random (random, randint, choice, shuffle, sample)
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# JSON MODULE
# =============================================================================

class TestJsonLoads:
    """Tests for json.loads()."""
    
    def test_loads_basic(self):
        """json.loads(s) → JSON.parse(s)"""
        result = transpile_expression('json.loads(data)')
        assert 'JSON.parse(data)' in result
    
    def test_loads_string_literal(self):
        """json.loads('{"key": "value"}')"""
        result = transpile_expression('json.loads(\'{"key": 1}\')')
        assert 'JSON.parse' in result
    
    def test_loads_in_assignment(self):
        """obj = json.loads(data)"""
        result = transpile('obj = json.loads(data)')
        assert 'JSON.parse' in result


class TestJsonDumps:
    """Tests for json.dumps()."""
    
    def test_dumps_basic(self):
        """json.dumps(obj) → JSON.stringify(obj)"""
        result = transpile_expression('json.dumps(data)')
        assert 'JSON.stringify(data' in result
    
    def test_dumps_with_indent(self):
        """json.dumps(obj, indent=2)"""
        result = transpile_expression('json.dumps(data, indent=2)')
        assert 'JSON.stringify' in result
        assert '2' in result
    
    def test_dumps_with_indent_4(self):
        """json.dumps(obj, indent=4)"""
        result = transpile_expression('json.dumps(data, indent=4)')
        assert 'JSON.stringify' in result
        assert '4' in result
    
    def test_dumps_with_sort_keys(self):
        """json.dumps(obj, sort_keys=True)"""
        result = transpile_expression('json.dumps(data, sort_keys=True)')
        assert '__py.json.dumps' in result or 'JSON.stringify' in result
    
    def test_dumps_in_assignment(self):
        """s = json.dumps(obj)"""
        result = transpile('s = json.dumps(obj)')
        assert 'JSON.stringify' in result


class TestJsonIntegration:
    """Integration tests for json module."""
    
    def test_loads_then_access(self):
        """json.loads(s)["key"]"""
        result = transpile_expression('json.loads(s)["key"]')
        assert 'JSON.parse' in result
        # Note: subscript may use __py.at for safety
        assert '"key"' in result
    
    def test_dumps_dict_literal(self):
        """json.dumps({"key": value})"""
        result = transpile_expression('json.dumps({"key": value})')
        assert 'JSON.stringify' in result


# =============================================================================
# MATH MODULE
# =============================================================================

class TestMathConstants:
    """Tests for math module constants.
    
    Note: Module attribute access (math.pi) is passed through as-is.
    The runtime __py.math.pi provides the values at execution time.
    Direct Math.* mapping only happens for function calls.
    """
    
    def test_math_pi(self):
        """math.pi - passed through for runtime evaluation"""
        result = transpile_expression('math.pi')
        # Passes through as math.pi (runtime provides __py.math.pi)
        assert 'math.pi' in result or 'Math.PI' in result
    
    def test_math_e(self):
        """math.e - passed through for runtime evaluation"""
        result = transpile_expression('math.e')
        assert 'math.e' in result or 'Math.E' in result
    
    def test_math_tau(self):
        """math.tau → (2 * Math.PI) for correct value"""
        result = transpile_expression('math.tau')
        assert 'Math.PI' in result or 'tau' in result
    
    def test_math_inf(self):
        """math.inf - passed through"""
        result = transpile_expression('math.inf')
        assert 'inf' in result or 'Infinity' in result
    
    def test_math_nan(self):
        """math.nan - passed through"""
        result = transpile_expression('math.nan')
        assert 'nan' in result or 'NaN' in result


class TestMathBasicFunctions:
    """Tests for basic math functions."""
    
    def test_math_floor(self):
        """math.floor(x) → Math.floor(x)"""
        result = transpile_expression('math.floor(3.7)')
        assert 'Math.floor(3.7)' in result
    
    def test_math_ceil(self):
        """math.ceil(x) → Math.ceil(x)"""
        result = transpile_expression('math.ceil(3.2)')
        assert 'Math.ceil(3.2)' in result
    
    def test_math_trunc(self):
        """math.trunc(x) → Math.trunc(x)"""
        result = transpile_expression('math.trunc(3.7)')
        assert 'Math.trunc(3.7)' in result
    
    def test_math_sqrt(self):
        """math.sqrt(x) → Math.sqrt(x)"""
        result = transpile_expression('math.sqrt(16)')
        assert 'Math.sqrt(16)' in result
    
    def test_math_abs(self):
        """math.fabs(x) → Math.abs(x)"""
        result = transpile_expression('math.fabs(-5)')
        # Negative literals may be wrapped in parentheses for precedence
        assert 'Math.abs(-5)' in result or 'Math.abs((-5))' in result
    
    def test_math_pow(self):
        """math.pow(x, y) → Math.pow(x, y)"""
        result = transpile_expression('math.pow(2, 10)')
        assert 'Math.pow(2, 10)' in result
    
    def test_math_exp(self):
        """math.exp(x) → Math.exp(x)"""
        result = transpile_expression('math.exp(1)')
        assert 'Math.exp(1)' in result


class TestMathLogFunctions:
    """Tests for logarithm functions."""
    
    def test_math_log_natural(self):
        """math.log(x) → Math.log(x)"""
        result = transpile_expression('math.log(10)')
        assert 'Math.log(10)' in result
    
    def test_math_log_with_base(self):
        """math.log(x, base) → Math.log(x) / Math.log(base)"""
        result = transpile_expression('math.log(100, 10)')
        assert 'Math.log' in result
    
    def test_math_log10(self):
        """math.log10(x) → Math.log10(x)"""
        result = transpile_expression('math.log10(100)')
        assert 'Math.log10(100)' in result
    
    def test_math_log2(self):
        """math.log2(x) → Math.log2(x)"""
        result = transpile_expression('math.log2(8)')
        assert 'Math.log2(8)' in result


class TestMathTrigFunctions:
    """Tests for trigonometric functions."""
    
    def test_math_sin(self):
        """math.sin(x) → Math.sin(x)"""
        result = transpile_expression('math.sin(0)')
        assert 'Math.sin(0)' in result
    
    def test_math_cos(self):
        """math.cos(x) → Math.cos(x)"""
        result = transpile_expression('math.cos(0)')
        assert 'Math.cos(0)' in result
    
    def test_math_tan(self):
        """math.tan(x) → Math.tan(x)"""
        result = transpile_expression('math.tan(0)')
        assert 'Math.tan(0)' in result
    
    def test_math_asin(self):
        """math.asin(x) → Math.asin(x)"""
        result = transpile_expression('math.asin(0)')
        assert 'Math.asin(0)' in result
    
    def test_math_acos(self):
        """math.acos(x) → Math.acos(x)"""
        result = transpile_expression('math.acos(1)')
        assert 'Math.acos(1)' in result
    
    def test_math_atan(self):
        """math.atan(x) → Math.atan(x)"""
        result = transpile_expression('math.atan(0)')
        assert 'Math.atan(0)' in result
    
    def test_math_atan2(self):
        """math.atan2(y, x) → Math.atan2(y, x)"""
        result = transpile_expression('math.atan2(1, 1)')
        assert 'Math.atan2(1, 1)' in result


class TestMathHyperbolicFunctions:
    """Tests for hyperbolic functions."""
    
    def test_math_sinh(self):
        """math.sinh(x) → Math.sinh(x)"""
        result = transpile_expression('math.sinh(0)')
        assert 'Math.sinh(0)' in result
    
    def test_math_cosh(self):
        """math.cosh(x) → Math.cosh(x)"""
        result = transpile_expression('math.cosh(0)')
        assert 'Math.cosh(0)' in result
    
    def test_math_tanh(self):
        """math.tanh(x) → Math.tanh(x)"""
        result = transpile_expression('math.tanh(0)')
        assert 'Math.tanh(0)' in result


class TestMathSpecialFunctions:
    """Tests for special math functions."""
    
    def test_math_degrees(self):
        """math.degrees(x) → x * (180 / Math.PI)"""
        result = transpile_expression('math.degrees(math.pi)')
        assert '180' in result or 'degrees' in result
    
    def test_math_radians(self):
        """math.radians(x) → x * (Math.PI / 180)"""
        result = transpile_expression('math.radians(180)')
        assert 'Math.PI' in result or 'radians' in result
    
    def test_math_hypot(self):
        """math.hypot(x, y) → Math.hypot(x, y)"""
        result = transpile_expression('math.hypot(3, 4)')
        assert 'Math.hypot(3, 4)' in result
    
    def test_math_isnan(self):
        """math.isnan(x) → Number.isNaN(x)"""
        result = transpile_expression('math.isnan(x)')
        assert 'Number.isNaN(x)' in result
    
    def test_math_isinf(self):
        """math.isinf(x) → !Number.isFinite(x)"""
        result = transpile_expression('math.isinf(x)')
        assert 'Number.isFinite' in result
    
    def test_math_isfinite(self):
        """math.isfinite(x) → Number.isFinite(x)"""
        result = transpile_expression('math.isfinite(x)')
        assert 'Number.isFinite(x)' in result


class TestMathAdvancedFunctions:
    """Tests for advanced math functions."""
    
    def test_math_factorial(self):
        """math.factorial(n) → __py.math.factorial(n)"""
        result = transpile_expression('math.factorial(5)')
        assert '__py.math.factorial(5)' in result
    
    def test_math_gcd(self):
        """math.gcd(a, b) → __py.math.gcd(a, b)"""
        result = transpile_expression('math.gcd(12, 18)')
        assert '__py.math.gcd(12, 18)' in result
    
    def test_math_lcm(self):
        """math.lcm(a, b) → __py.math.lcm(a, b)"""
        result = transpile_expression('math.lcm(4, 6)')
        assert '__py.math.lcm(4, 6)' in result


# =============================================================================
# RE MODULE
# =============================================================================

class TestReMatch:
    """Tests for re.match()."""
    
    def test_match_basic(self):
        """re.match(pattern, string) → __py.re.match(pattern, string)"""
        result = transpile_expression('re.match(r"\\d+", text)')
        assert '__py.re.match' in result
    
    def test_match_in_if(self):
        """if re.match(pattern, s): ..."""
        result = transpile('if re.match(r"\\d+", s):\n    pass')
        assert '__py.re.match' in result
    
    def test_match_assignment(self):
        """m = re.match(pattern, s)"""
        result = transpile('m = re.match(r"\\w+", s)')
        assert '__py.re.match' in result


class TestReSearch:
    """Tests for re.search()."""
    
    def test_search_basic(self):
        """re.search(pattern, string) → __py.re.search(pattern, string)"""
        result = transpile_expression('re.search(r"\\d+", text)')
        assert '__py.re.search' in result
    
    def test_search_in_if(self):
        """if re.search(pattern, s): ..."""
        result = transpile('if re.search(r"error", log):\n    pass')
        assert '__py.re.search' in result


class TestReSub:
    """Tests for re.sub()."""
    
    def test_sub_basic(self):
        """re.sub(pattern, repl, string) → __py.re.sub(pattern, repl, string)"""
        result = transpile_expression('re.sub(r"\\s+", " ", text)')
        assert '__py.re.sub' in result
    
    def test_sub_with_count(self):
        """re.sub(pattern, repl, string, count=1)"""
        result = transpile_expression('re.sub(r"x", "y", text, 1)')
        assert '__py.re.sub' in result
    
    def test_sub_in_assignment(self):
        """clean = re.sub(r"\\s+", " ", text)"""
        result = transpile('clean = re.sub(r"\\s+", " ", text)')
        assert '__py.re.sub' in result


class TestReFindall:
    """Tests for re.findall()."""
    
    def test_findall_basic(self):
        """re.findall(pattern, string) → __py.re.findall(pattern, string)"""
        result = transpile_expression('re.findall(r"\\d+", text)')
        assert '__py.re.findall' in result
    
    def test_findall_in_for(self):
        """for match in re.findall(pattern, s): ..."""
        result = transpile('for m in re.findall(r"\\w+", s):\n    pass')
        assert '__py.re.findall' in result


class TestReSplit:
    """Tests for re.split()."""
    
    def test_split_basic(self):
        """re.split(pattern, string) → __py.re.split(pattern, string)"""
        result = transpile_expression('re.split(r"\\s+", text)')
        assert '__py.re.split' in result
    
    def test_split_with_maxsplit(self):
        """re.split(pattern, string, maxsplit=2)"""
        result = transpile_expression('re.split(r",", text, 2)')
        assert '__py.re.split' in result


class TestReOther:
    """Tests for other re functions."""
    
    def test_escape(self):
        """re.escape(s) → __py.re.escape(s)"""
        result = transpile_expression('re.escape(pattern)')
        assert '__py.re.escape' in result
    
    def test_compile(self):
        """re.compile(pattern) → __py.re.compile(pattern)"""
        result = transpile_expression('re.compile(r"\\d+")')
        assert '__py.re.compile' in result
    
    def test_fullmatch(self):
        """re.fullmatch(pattern, string) → __py.re.fullmatch(pattern, string)"""
        result = transpile_expression('re.fullmatch(r"\\d+", text)')
        assert '__py.re.fullmatch' in result


# =============================================================================
# RANDOM MODULE
# =============================================================================

class TestRandomBasic:
    """Tests for basic random functions."""
    
    def test_random_random(self):
        """random.random() → Math.random()"""
        result = transpile_expression('random.random()')
        assert 'Math.random()' in result
    
    def test_random_randint(self):
        """random.randint(a, b) → __py.random.randint(a, b)"""
        result = transpile_expression('random.randint(1, 10)')
        assert '__py.random.randint(1, 10)' in result
    
    def test_random_randrange(self):
        """random.randrange(start, stop, step)"""
        result = transpile_expression('random.randrange(0, 100, 5)')
        assert '__py.random.randrange' in result
    
    def test_random_uniform(self):
        """random.uniform(a, b) → __py.random.uniform(a, b)"""
        result = transpile_expression('random.uniform(0.0, 1.0)')
        assert '__py.random.uniform' in result


class TestRandomChoice:
    """Tests for random.choice()."""
    
    def test_choice_basic(self):
        """random.choice(seq) → __py.random.choice(seq)"""
        result = transpile_expression('random.choice(items)')
        assert '__py.random.choice(items)' in result
    
    def test_choice_list_literal(self):
        """random.choice([1, 2, 3])"""
        result = transpile_expression('random.choice([1, 2, 3])')
        assert '__py.random.choice' in result


class TestRandomChoices:
    """Tests for random.choices()."""
    
    def test_choices_basic(self):
        """random.choices(population, k=3)"""
        result = transpile_expression('random.choices(items, 3)')
        assert '__py.random.choices' in result
    
    def test_choices_with_weights(self):
        """random.choices(population, weights=weights, k=3)"""
        result = transpile_expression('random.choices(items, 3, weights=w)')
        assert '__py.random.choices' in result


class TestRandomSample:
    """Tests for random.sample()."""
    
    def test_sample_basic(self):
        """random.sample(population, k) → __py.random.sample(population, k)"""
        result = transpile_expression('random.sample(items, 3)')
        assert '__py.random.sample(items, 3)' in result
    
    def test_sample_list_literal(self):
        """random.sample([1, 2, 3, 4, 5], 2)"""
        result = transpile_expression('random.sample([1, 2, 3, 4, 5], 2)')
        assert '__py.random.sample' in result


class TestRandomShuffle:
    """Tests for random.shuffle()."""
    
    def test_shuffle_basic(self):
        """random.shuffle(items) → __py.random.shuffle(items)"""
        result = transpile_expression('random.shuffle(items)')
        assert '__py.random.shuffle(items)' in result
    
    def test_shuffle_in_statement(self):
        """random.shuffle(deck)"""
        result = transpile('random.shuffle(deck)')
        assert '__py.random.shuffle' in result


class TestRandomDistributions:
    """Tests for random distribution functions."""
    
    def test_gauss(self):
        """random.gauss(mu, sigma) → __py.random.gauss(mu, sigma)"""
        result = transpile_expression('random.gauss(0, 1)')
        assert '__py.random.gauss(0, 1)' in result
    
    def test_normalvariate(self):
        """random.normalvariate(mu, sigma)"""
        result = transpile_expression('random.normalvariate(0, 1)')
        assert '__py.random.gauss(0, 1)' in result
    
    def test_seed(self):
        """random.seed(42) → __py.random.seed(42)"""
        result = transpile_expression('random.seed(42)')
        assert '__py.random.seed(42)' in result


# =============================================================================
# STDLIB INTEGRATION TESTS
# =============================================================================

class TestStdlibIntegration:
    """Integration tests combining stdlib modules."""
    
    def test_json_with_math(self):
        """json.dumps({"pi": math.pi})"""
        result = transpile_expression('json.dumps({"pi": math.pi})')
        assert 'JSON.stringify' in result
        # math.pi passes through for runtime evaluation
        assert 'math.pi' in result or 'Math.PI' in result
    
    def test_re_with_random(self):
        """Combining re and random"""
        result = transpile_expression('re.findall(r"\\d", str(random.randint(1, 100)))')
        assert '__py.re.findall' in result
        assert '__py.random.randint' in result
    
    def test_math_in_comprehension(self):
        """[math.sqrt(x) for x in items]"""
        result = transpile_expression('[math.sqrt(x) for x in items]')
        assert 'Math.sqrt' in result
    
    def test_json_loads_then_iterate(self):
        """for item in json.loads(data): ..."""
        result = transpile('for item in json.loads(data):\n    pass')
        assert 'JSON.parse' in result
    
    def test_random_in_sorted(self):
        """sorted(items, key=lambda x: random.random())"""
        result = transpile_expression('sorted(items, key=lambda x: random.random())')
        assert '__py.sorted' in result
        assert 'Math.random' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestStdlibEdgeCases:
    """Edge cases for stdlib modules."""
    
    def test_json_empty_object(self):
        """json.dumps({})"""
        result = transpile_expression('json.dumps({})')
        assert 'JSON.stringify' in result
    
    def test_json_empty_array(self):
        """json.dumps([])"""
        result = transpile_expression('json.dumps([])')
        assert 'JSON.stringify' in result
    
    def test_math_with_negative(self):
        """math.sqrt(-1) would be NaN"""
        result = transpile_expression('math.sqrt(x)')
        assert 'Math.sqrt(x)' in result
    
    def test_re_empty_pattern(self):
        """re.match("", s)"""
        result = transpile_expression('re.match("", s)')
        assert '__py.re.match' in result
    
    def test_random_single_item(self):
        """random.choice([1])"""
        result = transpile_expression('random.choice([x])')
        assert '__py.random.choice' in result
    
    def test_random_sample_zero(self):
        """random.sample(items, 0)"""
        result = transpile_expression('random.sample(items, 0)')
        assert '__py.random.sample' in result


# =============================================================================
# MODULE ATTRIBUTE ACCESS
# =============================================================================

class TestModuleAttributes:
    """Tests for accessing module attributes.
    
    Note: Module attributes pass through for runtime evaluation.
    The __py.math namespace provides the values at execution time.
    """
    
    def test_math_constant_in_expression(self):
        """x = 2 * math.pi"""
        result = transpile('x = 2 * math.pi')
        # math.pi passes through (runtime provides value)
        assert 'math.pi' in result or 'Math.PI' in result
    
    def test_nested_function_call(self):
        """math.sin(math.radians(45))"""
        result = transpile_expression('math.sin(math.radians(45))')
        assert 'Math.sin' in result
    
    def test_chained_json(self):
        """json.loads(json.dumps(obj))"""
        result = transpile_expression('json.loads(json.dumps(obj))')
        assert 'JSON.parse' in result
        assert 'JSON.stringify' in result
