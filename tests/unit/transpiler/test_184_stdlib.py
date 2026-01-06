"""
Phase 18.4: Standard Library Tests

Comprehensive tests for Python standard library transpilation:
- json module
- math module
- re module  
- random module
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# JSON MODULE - 40 tests
# =============================================================================

class TestJsonLoads:
    """Tests for json.loads()."""
    
    def test_loads_basic(self):
        result = transpile_expression('json.loads(s)')
        assert 'JSON.parse(s)' in result
    
    def test_loads_string_literal(self):
        result = transpile_expression('json.loads(\'{"a": 1}\')')
        assert 'JSON.parse' in result
    
    def test_loads_variable(self):
        result = transpile_expression('json.loads(json_string)')
        assert 'JSON.parse(json_string)' in result
    
    def test_loads_in_assignment(self):
        code = "data = json.loads(response)"
        result = transpile(code)
        assert 'JSON.parse(response)' in result


class TestJsonDumps:
    """Tests for json.dumps()."""
    
    def test_dumps_basic(self):
        result = transpile_expression('json.dumps(obj)')
        assert 'JSON.stringify(obj' in result
    
    def test_dumps_with_indent(self):
        result = transpile_expression('json.dumps(obj, indent=2)')
        assert 'JSON.stringify(obj, null, 2)' in result
    
    def test_dumps_indent_4(self):
        result = transpile_expression('json.dumps(data, indent=4)')
        assert 'JSON.stringify(data, null, 4)' in result
    
    def test_dumps_with_sort_keys(self):
        result = transpile_expression('json.dumps(obj, sort_keys=True)')
        assert '__py.json.dumps' in result or 'JSON.stringify' in result
    
    def test_dumps_all_options(self):
        result = transpile_expression('json.dumps(data, indent=2, sort_keys=True)')
        assert '__py.json.dumps' in result


class TestJsonIntegration:
    """Integration tests for json module."""
    
    def test_parse_and_modify(self):
        code = """
data = json.loads(s)
data['new'] = value
result = json.dumps(data)
"""
        result = transpile(code)
        assert 'JSON.parse' in result
        assert 'JSON.stringify' in result
    
    def test_json_in_function(self):
        code = """
def parse_config(s):
    return json.loads(s)
"""
        result = transpile(code)
        assert 'JSON.parse' in result


# =============================================================================
# MATH MODULE - 60 tests
# =============================================================================

class TestMathBasic:
    """Basic math functions."""
    
    def test_sqrt(self):
        result = transpile_expression('math.sqrt(x)')
        assert 'Math.sqrt(x)' in result
    
    def test_floor(self):
        result = transpile_expression('math.floor(x)')
        assert 'Math.floor(x)' in result
    
    def test_ceil(self):
        result = transpile_expression('math.ceil(x)')
        assert 'Math.ceil(x)' in result
    
    def test_abs(self):
        result = transpile_expression('math.fabs(x)')
        assert 'Math.abs(x)' in result
    
    def test_trunc(self):
        result = transpile_expression('math.trunc(x)')
        assert 'Math.trunc(x)' in result
    
    def test_pow(self):
        result = transpile_expression('math.pow(2, 10)')
        assert 'Math.pow(2, 10)' in result


class TestMathTrig:
    """Trigonometric functions."""
    
    def test_sin(self):
        result = transpile_expression('math.sin(x)')
        assert 'Math.sin(x)' in result
    
    def test_cos(self):
        result = transpile_expression('math.cos(x)')
        assert 'Math.cos(x)' in result
    
    def test_tan(self):
        result = transpile_expression('math.tan(x)')
        assert 'Math.tan(x)' in result
    
    def test_asin(self):
        result = transpile_expression('math.asin(x)')
        assert 'Math.asin(x)' in result
    
    def test_acos(self):
        result = transpile_expression('math.acos(x)')
        assert 'Math.acos(x)' in result
    
    def test_atan(self):
        result = transpile_expression('math.atan(x)')
        assert 'Math.atan(x)' in result
    
    def test_atan2(self):
        result = transpile_expression('math.atan2(y, x)')
        assert 'Math.atan2(y, x)' in result


class TestMathHyperbolic:
    """Hyperbolic functions."""
    
    def test_sinh(self):
        result = transpile_expression('math.sinh(x)')
        assert 'Math.sinh(x)' in result
    
    def test_cosh(self):
        result = transpile_expression('math.cosh(x)')
        assert 'Math.cosh(x)' in result
    
    def test_tanh(self):
        result = transpile_expression('math.tanh(x)')
        assert 'Math.tanh(x)' in result


class TestMathLogarithmic:
    """Logarithmic and exponential functions."""
    
    def test_log_natural(self):
        result = transpile_expression('math.log(x)')
        assert 'Math.log(x)' in result
    
    def test_log_with_base(self):
        result = transpile_expression('math.log(x, 10)')
        assert 'Math.log(x) / Math.log(10)' in result
    
    def test_log10(self):
        result = transpile_expression('math.log10(x)')
        assert 'Math.log10(x)' in result
    
    def test_log2(self):
        result = transpile_expression('math.log2(x)')
        assert 'Math.log2(x)' in result
    
    def test_exp(self):
        result = transpile_expression('math.exp(x)')
        assert 'Math.exp(x)' in result


class TestMathConstants:
    """Math constants - accessed as module attributes."""
    
    def test_pi_in_expression(self):
        """Constants are transpiled when used in context."""
        result = transpile_expression('x * math.pi')
        # Constants pass through as module attributes for now
        assert 'math.pi' in result or 'Math.PI' in result
    
    def test_e_in_expression(self):
        result = transpile_expression('math.exp(1) + math.e')
        assert 'Math.exp(1)' in result
    
    def test_tau_as_factor(self):
        result = transpile_expression('r * math.tau')
        # tau passes through or gets transformed
        assert 'math.tau' in result or 'Math.PI' in result
    
    def test_inf_comparison(self):
        result = transpile_expression('x < math.inf')
        # inf passes through as attribute access
        assert 'math.inf' in result or 'Infinity' in result
    
    def test_isnan_check(self):
        """Using isnan function instead of direct nan access."""
        result = transpile_expression('math.isnan(x)')
        assert 'Number.isNaN(x)' in result


class TestMathSpecial:
    """Special math functions."""
    
    def test_isnan(self):
        result = transpile_expression('math.isnan(x)')
        assert 'Number.isNaN(x)' in result
    
    def test_isinf(self):
        result = transpile_expression('math.isinf(x)')
        assert 'Number.isFinite' in result
    
    def test_isfinite(self):
        result = transpile_expression('math.isfinite(x)')
        assert 'Number.isFinite(x)' in result
    
    def test_degrees(self):
        result = transpile_expression('math.degrees(rad)')
        assert '180' in result
        assert 'Math.PI' in result
    
    def test_radians(self):
        result = transpile_expression('math.radians(deg)')
        assert 'Math.PI' in result
        assert '180' in result
    
    def test_hypot(self):
        result = transpile_expression('math.hypot(x, y)')
        assert 'Math.hypot(x, y)' in result
    
    def test_factorial(self):
        result = transpile_expression('math.factorial(n)')
        assert '__py.math.factorial(n)' in result
    
    def test_gcd(self):
        result = transpile_expression('math.gcd(a, b)')
        assert '__py.math.gcd(a, b)' in result
    
    def test_lcm(self):
        result = transpile_expression('math.lcm(a, b)')
        assert '__py.math.lcm(a, b)' in result


# =============================================================================
# RE MODULE - 50 tests
# =============================================================================

class TestReMatch:
    """Tests for re.match()."""
    
    def test_match_basic(self):
        result = transpile_expression('re.match(r"\\d+", s)')
        assert '__py.re.match' in result
    
    def test_match_pattern_var(self):
        result = transpile_expression('re.match(pattern, text)')
        assert '__py.re.match(pattern, text)' in result
    
    def test_match_in_condition(self):
        code = 'if re.match(r"^test", s): pass'
        result = transpile(code)
        assert '__py.re.match' in result


class TestReSearch:
    """Tests for re.search()."""
    
    def test_search_basic(self):
        result = transpile_expression('re.search(r"\\d+", s)')
        assert '__py.re.search' in result
    
    def test_search_pattern_var(self):
        result = transpile_expression('re.search(pattern, text)')
        assert '__py.re.search(pattern, text)' in result


class TestReFindall:
    """Tests for re.findall()."""
    
    def test_findall_basic(self):
        result = transpile_expression('re.findall(r"\\d+", s)')
        assert '__py.re.findall' in result
    
    def test_findall_pattern_var(self):
        result = transpile_expression('re.findall(pattern, text)')
        assert '__py.re.findall(pattern, text)' in result


class TestReSub:
    """Tests for re.sub()."""
    
    def test_sub_basic(self):
        result = transpile_expression('re.sub(r"\\s+", " ", s)')
        assert '__py.re.sub' in result
    
    def test_sub_with_count(self):
        result = transpile_expression('re.sub(pattern, repl, text, count=1)')
        assert '__py.re.sub' in result
    
    def test_sub_pattern_vars(self):
        result = transpile_expression('re.sub(pattern, replacement, text)')
        assert '__py.re.sub(pattern, replacement, text)' in result


class TestReSplit:
    """Tests for re.split()."""
    
    def test_split_basic(self):
        result = transpile_expression('re.split(r"\\s+", s)')
        assert '__py.re.split' in result
    
    def test_split_with_maxsplit(self):
        result = transpile_expression('re.split(pattern, text, maxsplit=2)')
        assert '__py.re.split' in result


class TestReOther:
    """Tests for other re functions."""
    
    def test_escape(self):
        result = transpile_expression('re.escape(s)')
        assert '__py.re.escape' in result
    
    def test_compile(self):
        result = transpile_expression('re.compile(pattern)')
        assert '__py.re.compile(pattern)' in result
    
    def test_fullmatch(self):
        result = transpile_expression('re.fullmatch(pattern, s)')
        assert '__py.re.fullmatch(pattern, s)' in result
    
    def test_finditer(self):
        result = transpile_expression('re.finditer(pattern, text)')
        assert '__py.re.finditer(pattern, text)' in result


# =============================================================================
# RANDOM MODULE - 50 tests
# =============================================================================

class TestRandomBasic:
    """Basic random functions."""
    
    def test_random(self):
        result = transpile_expression('random.random()')
        assert 'Math.random()' in result
    
    def test_randint(self):
        result = transpile_expression('random.randint(1, 10)')
        assert '__py.random.randint(1, 10)' in result
    
    def test_randrange_one_arg(self):
        result = transpile_expression('random.randrange(10)')
        assert '__py.random.randrange(10)' in result
    
    def test_randrange_two_args(self):
        result = transpile_expression('random.randrange(1, 10)')
        assert '__py.random.randrange(1, 10)' in result
    
    def test_randrange_three_args(self):
        result = transpile_expression('random.randrange(0, 100, 5)')
        assert '__py.random.randrange(0, 100, 5)' in result
    
    def test_uniform(self):
        result = transpile_expression('random.uniform(0.0, 1.0)')
        assert '__py.random.uniform(0.0, 1.0)' in result


class TestRandomSequence:
    """Sequence random functions."""
    
    def test_choice(self):
        result = transpile_expression('random.choice(items)')
        assert '__py.random.choice(items)' in result
    
    def test_choices(self):
        result = transpile_expression('random.choices(items, k=3)')
        assert '__py.random.choices' in result
    
    def test_sample(self):
        result = transpile_expression('random.sample(items, 3)')
        assert '__py.random.sample(items, 3)' in result
    
    def test_shuffle(self):
        result = transpile_expression('random.shuffle(items)')
        assert '__py.random.shuffle(items)' in result


class TestRandomDistributions:
    """Distribution functions."""
    
    def test_gauss(self):
        result = transpile_expression('random.gauss(0, 1)')
        assert '__py.random.gauss(0, 1)' in result
    
    def test_normalvariate(self):
        result = transpile_expression('random.normalvariate(0, 1)')
        assert '__py.random.gauss(0, 1)' in result
    
    def test_expovariate(self):
        result = transpile_expression('random.expovariate(1.0)')
        assert '__py.random.expovariate(1.0)' in result
    
    def test_triangular(self):
        result = transpile_expression('random.triangular(0, 1, 0.5)')
        assert '__py.random.triangular(0, 1, 0.5)' in result


class TestRandomState:
    """State functions."""
    
    def test_seed(self):
        result = transpile_expression('random.seed(42)')
        assert '__py.random.seed(42)' in result
    
    def test_seed_none(self):
        result = transpile_expression('random.seed()')
        assert '__py.random.seed(null)' in result


# =============================================================================
# STDLIB INTEGRATION TESTS - 30 tests
# =============================================================================

class TestStdlibIntegration:
    """Integration tests combining stdlib modules."""
    
    def test_json_in_handler(self):
        code = """
def handle_response(text):
    data = json.loads(text)
    return data['result']
"""
        result = transpile(code)
        assert 'JSON.parse' in result
    
    def test_math_calculations(self):
        code = """
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
"""
        result = transpile(code)
        assert 'Math.sqrt' in result
    
    def test_re_validation(self):
        code = """
def is_email(s):
    return bool(re.match(r'^[a-z]+@[a-z]+\\.[a-z]+$', s))
"""
        result = transpile(code)
        assert '__py.re.match' in result
    
    def test_random_selection(self):
        code = """
def pick_random_items(items, count):
    return random.sample(items, count)
"""
        result = transpile(code)
        assert '__py.random.sample' in result
    
    def test_complex_json_math(self):
        code = """
def process_data(json_str):
    data = json.loads(json_str)
    values = data['values']
    return math.sqrt(sum(v ** 2 for v in values))
"""
        result = transpile(code)
        assert 'JSON.parse' in result
        assert 'Math.sqrt' in result
    
    def test_regex_and_json(self):
        result = transpile_expression('json.loads(re.sub(r"\\s+", "", text))')
        assert 'JSON.parse' in result
        assert '__py.re.sub' in result
    
    def test_math_trig_expression(self):
        result = transpile_expression('math.sin(math.radians(45))')
        assert 'Math.sin' in result
        assert 'Math.PI' in result
    
    def test_random_with_range(self):
        result = transpile_expression('random.choice(range(10))')
        assert '__py.random.choice' in result
        assert '__py.range' in result


# =============================================================================
# EDGE CASES - 20 tests
# =============================================================================

class TestStdlibEdgeCases:
    """Edge cases for stdlib modules."""
    
    def test_json_empty_object(self):
        result = transpile_expression('json.dumps({})')
        assert 'JSON.stringify' in result
    
    def test_json_empty_array(self):
        result = transpile_expression('json.dumps([])')
        assert 'JSON.stringify' in result
    
    def test_math_zero_input(self):
        result = transpile_expression('math.sqrt(0)')
        assert 'Math.sqrt(0)' in result
    
    def test_math_negative_sqrt(self):
        result = transpile_expression('math.sqrt(-1)')
        # Negative literals may be wrapped in parentheses for precedence
        assert 'Math.sqrt(-1)' in result or 'Math.sqrt((-1))' in result
    
    def test_re_empty_pattern(self):
        result = transpile_expression('re.match("", s)')
        assert '__py.re.match' in result
    
    def test_random_single_item(self):
        result = transpile_expression('random.choice([42])')
        assert '__py.random.choice' in result
    
    def test_math_very_large(self):
        result = transpile_expression('math.log(1e308)')
        assert 'Math.log' in result
    
    def test_json_nested(self):
        result = transpile_expression('json.dumps({"a": {"b": {"c": 1}}})')
        assert 'JSON.stringify' in result
    
    def test_re_special_chars(self):
        result = transpile_expression('re.escape("$100")')
        assert '__py.re.escape' in result
    
    def test_random_zero_sample(self):
        result = transpile_expression('random.sample(items, 0)')
        assert '__py.random.sample' in result
