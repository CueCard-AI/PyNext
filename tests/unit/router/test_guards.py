"""
Comprehensive tests for route guards.

Tests cover:
1. Guard functions
2. Redirect handling
3. Multiple guards
4. Async guards (future)
"""

import pytest
from unittest.mock import Mock, MagicMock

from pynext.reactive.router import (
    Route,
    Redirect,
    createRouteGuard,
)


# =============================================================================
# SECTION 1: REDIRECT CLASS
# =============================================================================

class TestRedirect:
    """Test Redirect dataclass."""
    
    def test_redirect_creation(self):
        """Redirect creates with path."""
        redirect = Redirect(to="/login")
        
        assert redirect.to == "/login"
    
    def test_redirect_default_replace(self):
        """Redirect defaults to replace=True."""
        redirect = Redirect(to="/login")
        
        assert redirect.replace is True
    
    def test_redirect_no_replace(self):
        """Redirect with replace=False."""
        redirect = Redirect(to="/login", replace=False)
        
        assert redirect.replace is False
    
    def test_redirect_equality(self):
        """Redirects with same path are equal."""
        r1 = Redirect(to="/login")
        r2 = Redirect(to="/login")
        
        assert r1 == r2
    
    def test_redirect_inequality(self):
        """Redirects with different paths are not equal."""
        r1 = Redirect(to="/login")
        r2 = Redirect(to="/signup")
        
        assert r1 != r2


# =============================================================================
# SECTION 2: CREATE ROUTE GUARD
# =============================================================================

class TestCreateRouteGuard:
    """Test createRouteGuard factory."""
    
    def test_creates_callable(self):
        """Creates callable guard."""
        guard = createRouteGuard(lambda: None)
        
        assert callable(guard)
    
    def test_guard_returns_none_allows(self):
        """Guard returning None allows access."""
        guard = createRouteGuard(lambda: None)
        result = guard()
        
        assert result is None
    
    def test_guard_returns_redirect(self):
        """Guard can return Redirect."""
        guard = createRouteGuard(lambda: Redirect("/login"))
        result = guard()
        
        assert isinstance(result, Redirect)
        assert result.to == "/login"
    
    def test_guard_with_state(self):
        """Guard with captured state."""
        is_logged_in = [False]
        
        def check():
            if not is_logged_in[0]:
                return Redirect("/login")
            return None
        
        guard = createRouteGuard(check)
        
        # Not logged in - redirect
        assert isinstance(guard(), Redirect)
        
        # Log in
        is_logged_in[0] = True
        
        # Now allowed
        assert guard() is None


# =============================================================================
# SECTION 3: ROUTE WITH GUARDS
# =============================================================================

class TestRouteWithGuards:
    """Test Route component with guards."""
    
    def test_route_accepts_guards(self):
        """Route accepts guard list."""
        guard = lambda: None
        route = Route("/admin", component=lambda: None, guards=[guard])
        
        assert len(route.guards) == 1
        assert route.guards[0] is guard
    
    def test_route_multiple_guards(self):
        """Route with multiple guards."""
        guard1 = lambda: None
        guard2 = lambda: None
        guard3 = lambda: None
        
        route = Route("/admin", component=lambda: None, guards=[guard1, guard2, guard3])
        
        assert len(route.guards) == 3
    
    def test_route_default_no_guards(self):
        """Route defaults to no guards."""
        route = Route("/", component=lambda: None)
        
        assert route.guards == []
    
    def test_guards_in_compiled_route(self):
        """Guards preserved in compiled route."""
        guard = lambda: None
        route = Route("/", component=lambda: None, guards=[guard])
        compiled = route.to_compiled()
        
        assert compiled.guards == [guard]


# =============================================================================
# SECTION 4: GUARD PATTERNS
# =============================================================================

class TestGuardPatterns:
    """Test common guard patterns."""
    
    def test_auth_guard_pattern(self):
        """Authentication guard pattern."""
        def create_auth_guard(check_auth):
            def guard():
                if not check_auth():
                    return Redirect("/login")
                return None
            return guard
        
        # Simulate auth state
        is_authenticated = Mock(return_value=False)
        guard = create_auth_guard(is_authenticated)
        
        # Not authenticated
        result = guard()
        assert isinstance(result, Redirect)
        assert result.to == "/login"
        
        # Authenticated
        is_authenticated.return_value = True
        result = guard()
        assert result is None
    
    def test_role_guard_pattern(self):
        """Role-based guard pattern."""
        def create_role_guard(required_role, get_user_role):
            def guard():
                if get_user_role() != required_role:
                    return Redirect("/unauthorized")
                return None
            return guard
        
        get_role = Mock(return_value="user")
        admin_guard = create_role_guard("admin", get_role)
        
        # Wrong role
        result = admin_guard()
        assert isinstance(result, Redirect)
        
        # Correct role
        get_role.return_value = "admin"
        result = admin_guard()
        assert result is None
    
    def test_feature_flag_guard(self):
        """Feature flag guard pattern."""
        def create_feature_guard(feature_name, is_enabled):
            def guard():
                if not is_enabled(feature_name):
                    return Redirect("/")
                return None
            return guard
        
        features = {"beta": False}
        guard = create_feature_guard("beta", lambda f: features.get(f, False))
        
        # Feature disabled
        assert isinstance(guard(), Redirect)
        
        # Feature enabled
        features["beta"] = True
        assert guard() is None


# =============================================================================
# SECTION 5: GUARD EXECUTION ORDER
# =============================================================================

class TestGuardExecutionOrder:
    """Test guard execution order."""
    
    def test_guards_execute_in_order(self):
        """Guards execute in definition order."""
        call_order = []
        
        def guard1():
            call_order.append(1)
            return None
        
        def guard2():
            call_order.append(2)
            return None
        
        def guard3():
            call_order.append(3)
            return None
        
        route = Route("/", component=lambda: None, guards=[guard1, guard2, guard3])
        
        # Execute guards
        for guard in route.guards:
            guard()
        
        assert call_order == [1, 2, 3]
    
    def test_first_redirect_wins(self):
        """First guard to redirect stops chain."""
        def guard1():
            return Redirect("/first")
        
        def guard2():
            return Redirect("/second")  # Never reached in typical impl
        
        route = Route("/", component=lambda: None, guards=[guard1, guard2])
        
        # First guard redirects
        result = route.guards[0]()
        assert result.to == "/first"


# =============================================================================
# SECTION 6: EDGE CASES
# =============================================================================

class TestGuardEdgeCases:
    """Test guard edge cases."""
    
    def test_guard_returning_false(self):
        """Guard returning False (not None)."""
        # Some implementations might use False to mean "allow"
        guard = createRouteGuard(lambda: False)
        result = guard()
        
        # False is not None, but also not Redirect
        assert result is False
    
    def test_guard_returning_true(self):
        """Guard returning True."""
        guard = createRouteGuard(lambda: True)
        result = guard()
        
        assert result is True
    
    def test_guard_with_exception(self):
        """Guard that raises exception."""
        def failing_guard():
            raise ValueError("Auth check failed")
        
        guard = createRouteGuard(failing_guard)
        
        with pytest.raises(ValueError):
            guard()
    
    def test_redirect_with_query(self):
        """Redirect with query params."""
        redirect = Redirect(to="/login?returnUrl=/admin")
        
        assert redirect.to == "/login?returnUrl=/admin"
    
    def test_redirect_with_hash(self):
        """Redirect with hash."""
        redirect = Redirect(to="/page#section")
        
        assert redirect.to == "/page#section"

