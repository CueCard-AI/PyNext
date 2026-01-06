"""
Phase 18.6 Form Transform Tests

=============================================================================
TEST COVERAGE: 60 tests for Form transforms
=============================================================================

Tests verify that form operations are correctly transformed to use the
__pynext__.getForm() API.

Transformations tested:
- form.validate() → __pynext__.getForm('id').validate()
- form.values → __pynext__.getForm('id').values
- form.reset() → __pynext__.getForm('id').reset()
- form.field_name → __pynext__.getForm('id').field_name
- form.errors → __pynext__.getForm('id').errors
"""

import pytest
from pynext.transpiler.reactive import create_context
from pynext.transpiler.pynext import transpile_handler_source


def transpile_with_context(code: str, ctx):
    """Helper to transpile code with a given reactive context."""
    return transpile_handler_source(code, ctx)


# =============================================================================
# FORM VALIDATION (10 tests)
# =============================================================================

class TestFormValidation:
    """Test form.validate() → __pynext__.getForm('id').validate()"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={"login_form": "form_1"})
    
    def test_simple_validate(self, ctx):
        """login_form.validate() → getForm().validate()"""
        code = "result = login_form.validate()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "form_1" in result  # May be single or double quotes
        assert ".validate()" in result
    
    def test_validate_in_condition(self, ctx):
        """if login_form.validate(): → if (getForm().validate())"""
        code = """
if login_form.validate():
    submit()
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".validate()" in result
    
    def test_validate_and_action(self, ctx):
        """if login_form.validate(): do_something()"""
        code = """
if login_form.validate():
    process(login_form.values)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getForm") >= 2
    
    def test_validate_with_else(self, ctx):
        """if form.validate(): ok() else: error()"""
        code = """
if login_form.validate():
    success()
else:
    show_errors()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_validate_return_value(self, ctx):
        """is_valid = form.validate()"""
        code = "is_valid = login_form.validate()"
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_validate_not(self, ctx):
        """if not form.validate(): show_error()"""
        code = """
if not login_form.validate():
    show_error()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_validate_and_reset(self, ctx):
        """if form.validate(): form.reset()"""
        code = """
if login_form.validate():
    process()
    login_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
        assert ".reset()" in result
    
    def test_validate_in_function(self, ctx):
        """def submit(): if form.validate(): ..."""
        code = """
def submit():
    if login_form.validate():
        return True
    return False
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_validate_save_result(self, ctx):
        """valid = form.validate(); if valid: ..."""
        code = """
valid = login_form.validate()
if valid:
    submit()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
    
    def test_validate_with_arguments(self, ctx):
        """form.validate() with captured args"""
        code = """
if login_form.validate():
    api.login(login_form.values)
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result


# =============================================================================
# FORM VALUES (10 tests)
# =============================================================================

class TestFormValues:
    """Test form.values → __pynext__.getForm('id').values"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={"user_form": "form_1"})
    
    def test_simple_values_access(self, ctx):
        """data = user_form.values → getForm().values"""
        code = "data = user_form.values"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".values" in result
    
    def test_values_property_access(self, ctx):
        """user_form.values["email"] → getForm().values["email"]"""
        code = 'email = user_form.values["email"]'
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_in_function_call(self, ctx):
        """submit(user_form.values) → submit(getForm().values)"""
        code = "submit(user_form.values)"
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_destructure(self, ctx):
        """email, password = form.values["email"], form.values["password"]"""
        code = """
email = user_form.values["email"]
password = user_form.values["password"]
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".values") >= 2
    
    def test_values_in_dict(self, ctx):
        """data = {"form": user_form.values} → {"form": getForm().values}"""
        code = '{"form": user_form.values}'
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_spread(self, ctx):
        """data = {**user_form.values, "extra": value}"""
        code = 'data = {**user_form.values, "extra": value}'
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_with_validation(self, ctx):
        """if form.validate(): process(form.values)"""
        code = """
if user_form.validate():
    process(user_form.values)
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
        assert ".validate()" in result
    
    def test_values_keys(self, ctx):
        """for key in user_form.values: print(key)"""
        code = """
for key in user_form.values:
    print(key)
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_items(self, ctx):
        """for k, v in user_form.values.items(): print(k, v)"""
        code = """
for k, v in user_form.values.items():
    print(k, v)
"""
        result = transpile_with_context(code, ctx)
        assert ".values" in result
    
    def test_values_get(self, ctx):
        """user_form.values.get("key", default)"""
        code = 'value = user_form.values.get("key", "default")'
        result = transpile_with_context(code, ctx)
        assert ".values" in result


# =============================================================================
# FORM RESET (10 tests)
# =============================================================================

class TestFormReset:
    """Test form.reset() → __pynext__.getForm('id').reset()"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={"contact_form": "form_1"})
    
    def test_simple_reset(self, ctx):
        """contact_form.reset() → getForm().reset()"""
        code = "contact_form.reset()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".reset()" in result
    
    def test_reset_after_validate(self, ctx):
        """if form.validate(): form.reset()"""
        code = """
if contact_form.validate():
    submit()
    contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_in_else(self, ctx):
        """if cond: submit() else: form.reset()"""
        code = """
if submitted:
    show_success()
else:
    contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_unconditional(self, ctx):
        """Always reset after action"""
        code = """
process()
contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_in_try(self, ctx):
        """try: submit() finally: form.reset()"""
        code = """
try:
    submit()
except:
    pass
contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_in_handler(self, ctx):
        """def handle_clear(): form.reset()"""
        code = """
def handle_clear():
    contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_multiple_times(self, ctx):
        """Reset called twice (shouldn't happen but handle it)"""
        code = """
contact_form.reset()
contact_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".reset()") >= 2
    
    def test_reset_with_validation_flow(self, ctx):
        """Full form flow with reset"""
        code = """
if contact_form.validate():
    api.submit(contact_form.values)
    contact_form.reset()
    show_success()
"""
        result = transpile_with_context(code, ctx)
        assert ".validate()" in result
        assert ".values" in result
        assert ".reset()" in result
    
    def test_reset_in_callback(self, ctx):
        """on_success = lambda: form.reset()"""
        code = "on_success = lambda: contact_form.reset()"
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_reset_return(self, ctx):
        """def handler(): form.reset(); return True"""
        code = """
def handler():
    contact_form.reset()
    return True
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result


# =============================================================================
# FORM FIELD ACCESS (10 tests)
# =============================================================================

class TestFormFieldAccess:
    """Test form.field_name → __pynext__.getForm('id').field_name"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={"issue_form": "form_1"})
    
    def test_field_read(self, ctx):
        """issue_form.title → getForm().title"""
        code = "title = issue_form.title"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".title" in result
    
    def test_field_read_call(self, ctx):
        """issue_form.title() → getForm().title.read()"""
        code = "title = issue_form.title()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
    
    def test_field_set(self, ctx):
        """issue_form.title.set("value") → getForm().title.set("value")"""
        code = 'issue_form.title.set("New Title")'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".set(" in result
    
    def test_multiple_fields(self, ctx):
        """Access multiple form fields"""
        code = """
title = issue_form.title
status = issue_form.status
priority = issue_form.priority
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getForm") >= 3
    
    def test_field_in_expression(self, ctx):
        """len(issue_form.title) → getForm().title.length"""
        code = "length = len(issue_form.title)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
    
    def test_field_comparison(self, ctx):
        """issue_form.title == "" → getForm().title === \"\""""
        code = 'is_empty = issue_form.title == ""'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
    
    def test_field_in_condition(self, ctx):
        """if issue_form.title: → if (getForm().title)"""
        code = """
if issue_form.title:
    submit()
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
    
    def test_field_clear(self, ctx):
        """issue_form.title.set("") → clear field"""
        code = 'issue_form.title.set("")'
        result = transpile_with_context(code, ctx)
        assert ".set(" in result
    
    def test_field_update(self, ctx):
        """issue_form.title.update(lambda s: s.strip())"""
        code = "issue_form.title.update(lambda s: s.strip())"
        result = transpile_with_context(code, ctx)
        assert ".update(" in result
    
    def test_field_to_dict(self, ctx):
        """{"title": issue_form.title} → {"title": getForm().title}"""
        code = '{"title": issue_form.title}'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result


# =============================================================================
# FORM ERRORS (10 tests)
# =============================================================================

class TestFormErrors:
    """Test form.errors → __pynext__.getForm('id').errors"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={"signup_form": "form_1"})
    
    def test_errors_access(self, ctx):
        """signup_form.errors → getForm().errors"""
        code = "errs = signup_form.errors"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert ".errors" in result
    
    def test_errors_field(self, ctx):
        """signup_form.errors.email → getForm().errors.email"""
        code = "email_error = signup_form.errors.email"
        result = transpile_with_context(code, ctx)
        assert ".errors" in result
    
    def test_errors_check(self, ctx):
        """if signup_form.errors: → if (getForm().errors)"""
        code = """
if signup_form.errors:
    show_errors()
"""
        result = transpile_with_context(code, ctx)
        assert ".errors" in result
    
    def test_error_for_field(self, ctx):
        """if signup_form.errors.email: show(error)"""
        code = """
if signup_form.errors.email:
    show_error(signup_form.errors.email)
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".errors") >= 2
    
    def test_errors_in_template(self, ctx):
        """{"error": signup_form.errors.email}"""
        code = '{"error": signup_form.errors.email}'
        result = transpile_with_context(code, ctx)
        assert ".errors" in result
    
    def test_errors_multiple_fields(self, ctx):
        """Check multiple error fields"""
        code = """
email_err = signup_form.errors.email
pass_err = signup_form.errors.password
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".errors") >= 2
    
    def test_errors_has_any(self, ctx):
        """any(signup_form.errors.values())"""
        code = "has_errors = any(signup_form.errors.values())"
        result = transpile_with_context(code, ctx)
        assert ".errors" in result
    
    def test_errors_display(self, ctx):
        """Display all errors"""
        code = """
for field, error in signup_form.errors.items():
    print(f"{field}: {error}")
"""
        result = transpile_with_context(code, ctx)
        assert ".errors" in result
    
    def test_errors_clear(self, ctx):
        """Clear errors via reset"""
        code = """
signup_form.reset()  # Clears errors too
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
    
    def test_errors_conditional(self, ctx):
        """signup_form.errors.email if not valid else ""."""
        code = 'error = signup_form.errors.email if not valid else ""'
        result = transpile_with_context(code, ctx)
        assert ".errors" in result


# =============================================================================
# MULTIPLE FORMS (5 tests)
# =============================================================================

class TestMultipleForms:
    """Test handlers with multiple forms."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(forms={
            "login_form": "form_1",
            "signup_form": "form_2",
        })
    
    def test_two_forms_validate(self, ctx):
        """Both forms validate"""
        code = """
login_valid = login_form.validate()
signup_valid = signup_form.validate()
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getForm") >= 2
    
    def test_two_forms_values(self, ctx):
        """Access values from both"""
        code = """
login_data = login_form.values
signup_data = signup_form.values
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".values") >= 2
    
    def test_two_forms_reset(self, ctx):
        """Reset both forms"""
        code = """
login_form.reset()
signup_form.reset()
"""
        result = transpile_with_context(code, ctx)
        assert result.count(".reset()") >= 2
    
    def test_form_switch(self, ctx):
        """Switch between forms based on condition"""
        code = """
if is_login:
    login_form.validate()
else:
    signup_form.validate()
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getForm") >= 2
    
    def test_forms_with_different_ids(self, ctx):
        """IDs should be preserved correctly"""
        code = """
login_form.validate()
signup_form.validate()
"""
        result = transpile_with_context(code, ctx)
        assert "form_1" in result
        assert "form_2" in result


# =============================================================================
# FORM WITH SIGNALS (5 tests)
# =============================================================================

class TestFormWithSignals:
    """Test handlers with forms and signals together."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(
            forms={"issue_form": "form_1"},
            signals={"show_modal": "sig_1", "all_issues": "sig_2"}
        )
    
    def test_form_validate_signal_set(self, ctx):
        """if form.validate(): signal.set(False)"""
        code = """
if issue_form.validate():
    show_modal.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
    
    def test_form_values_signal_update(self, ctx):
        """signal.set([*signal(), form.values])"""
        code = """
if issue_form.validate():
    values = issue_form.values
    all_issues.set([*all_issues(), values])
    issue_form.reset()
    show_modal.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
    
    def test_signal_controls_form(self, ctx):
        """if show_modal(): form.validate()"""
        code = """
if show_modal():
    issue_form.validate()
"""
        result = transpile_with_context(code, ctx)
        assert ".read()" in result or "__pynext__.getSignal" in result
        assert ".validate()" in result
    
    def test_form_reset_signal_update(self, ctx):
        """form.reset(); signal.set(True)"""
        code = """
issue_form.reset()
show_modal.set(True)
"""
        result = transpile_with_context(code, ctx)
        assert ".reset()" in result
        assert ".set(true)" in result or ".set(True)" in result
    
    def test_full_add_issue_pattern(self, ctx):
        """The handle_add_issue pattern that was failing"""
        code = """
if issue_form.validate():
    values = issue_form.values
    new_issue = {"title": values["title"]}
    all_issues.set([*all_issues(), new_issue])
    issue_form.reset()
    show_modal.set(False)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getForm" in result
        assert "__pynext__.getSignal" in result
        assert ".validate()" in result
        assert ".values" in result
        assert ".reset()" in result
        assert ".set(" in result
