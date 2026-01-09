# Phase 34.1: Core DOM APIs - Test Overview

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 125 |
| **Unit Tests** | 108 |
| **Integration Tests** | 17 |
| **Pass Rate** | 100% |

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/client/test_341_document.py` | 31 | Document queries, creation, properties |
| `tests/unit/client/test_341_element_attrs.py` | 22 | Attributes, dataset, classList |
| `tests/unit/client/test_341_element_content.py` | 16 | innerHTML, textContent, value |
| `tests/unit/client/test_341_traversal.py` | 20 | DOM tree navigation |
| `tests/unit/client/test_341_manipulation.py` | 19 | DOM mutations |
| `tests/integration/transpiler/test_341_dom_parity.py` | 17 | Mini-app patterns |

## Test Categories

### Document Tests (31 tests)

**Queries (12 tests)**
- `test_get_element_by_id_basic` - Basic getElementById transpilation
- `test_get_element_by_id_transpiles_directly` - Clean output verification
- `test_get_element_by_id_no_runtime_wrapper` - No `__py.*` in output
- `test_query_selector_class` - querySelector with class selector
- `test_query_selector_id` - querySelector with ID selector
- `test_query_selector_complex` - Complex CSS selectors
- `test_query_selector_all_basic` - querySelectorAll basic
- `test_query_selector_all_transpiles_directly` - Clean transpilation
- `test_get_elements_by_class_name` - getElementsByClassName
- `test_get_elements_by_tag_name` - getElementsByTagName
- `test_get_elements_by_name` - getElementsByName
- `test_chained_queries` - Query chaining

**Creation (8 tests)**
- `test_create_element_div` - createElement for div
- `test_create_element_span` - createElement for span
- `test_create_element_ns_svg` - createElementNS for SVG
- `test_create_element_ns_mathml` - createElementNS for MathML
- `test_create_text_node` - createTextNode
- `test_create_comment` - createComment
- `test_create_document_fragment` - createDocumentFragment
- `test_create_and_append_chain` - Create + append pattern

**Properties (11 tests)**
- `test_document_body` - document.body access
- `test_document_head` - document.head access
- `test_document_document_element` - documentElement
- `test_document_title_read` - Read title
- `test_document_title_write` - Write title
- `test_document_active_element` - activeElement
- `test_document_ready_state` - readyState
- `test_document_hidden` - hidden property
- `test_document_visibility_state` - visibilityState
- `test_document_cookie_read` - Read cookie
- `test_document_cookie_write` - Write cookie

### Element Attribute Tests (22 tests)

**Attributes (10 tests)**
- `test_get_attribute` - getAttribute
- `test_set_attribute` - setAttribute
- `test_remove_attribute` - removeAttribute
- `test_has_attribute_true` - hasAttribute returns true
- `test_has_attribute_false` - hasAttribute in condition
- `test_toggle_attribute_on` - toggleAttribute basic
- `test_toggle_attribute_off` - toggleAttribute toggle off
- `test_toggle_attribute_force_true` - toggleAttribute force add
- `test_toggle_attribute_force_false` - toggleAttribute force remove
- `test_get_attribute_names` - getAttributeNames

**Dataset (3 tests)**
- `test_dataset_read_single` - Read data attribute
- `test_dataset_read_camel_case` - CamelCase conversion
- `test_dataset_write` - Write data attribute

**ClassList (9 tests)**
- `test_class_list_add` - classList.add single
- `test_class_list_add_multiple` - classList.add multiple
- `test_class_list_remove` - classList.remove
- `test_class_list_toggle` - classList.toggle
- `test_class_list_toggle_force` - classList.toggle with force
- `test_class_list_contains` - classList.contains
- `test_class_list_replace` - classList.replace
- `test_class_name_read` - className read
- `test_class_name_write` - className write

### Element Content Tests (16 tests)

- `test_inner_html_read` - Read innerHTML
- `test_inner_html_write` - Write innerHTML
- `test_inner_html_with_variable` - innerHTML with variable
- `test_outer_html_read` - Read outerHTML
- `test_inner_text_read` - Read innerText
- `test_inner_text_write` - Write innerText
- `test_text_content_read` - Read textContent
- `test_text_content_write` - Write textContent
- `test_value_input` - Input value
- `test_value_textarea` - Textarea value
- `test_id_read` - Read id
- `test_id_write` - Write id
- `test_tag_name` - tagName
- `test_hidden_read` - Read hidden
- `test_hidden_write` - Write hidden
- `test_tab_index` - tabIndex

### DOM Traversal Tests (20 tests)

- `test_parent_element` - parentElement
- `test_parent_node` - parentNode
- `test_children` - children collection
- `test_child_nodes` - childNodes
- `test_first_element_child` - firstElementChild
- `test_last_element_child` - lastElementChild
- `test_first_child` - firstChild
- `test_last_child` - lastChild
- `test_next_element_sibling` - nextElementSibling
- `test_previous_element_sibling` - previousElementSibling
- `test_next_sibling` - nextSibling
- `test_previous_sibling` - previousSibling
- `test_closest_immediate` - closest() immediate parent
- `test_closest_ancestor` - closest() ancestor
- `test_closest_not_found` - closest() returns null
- `test_matches_true` - matches() returns true
- `test_matches_false` - matches() in condition
- `test_child_element_count` - childElementCount
- `test_is_connected` - isConnected
- `test_owner_document` - ownerDocument

### DOM Manipulation Tests (19 tests)

**Basic Manipulation (17 tests)**
- `test_append_child` - appendChild
- `test_insert_before` - insertBefore
- `test_remove_child` - removeChild
- `test_replace_child` - replaceChild
- `test_remove_self` - element.remove()
- `test_clone_node_shallow` - cloneNode shallow
- `test_clone_node_deep` - cloneNode deep
- `test_append_multiple` - append() multiple nodes
- `test_append_with_string` - append() with strings
- `test_prepend` - prepend()
- `test_after` - after()
- `test_before` - before()
- `test_replace_with` - replaceWith()
- `test_replace_children` - replaceChildren()
- `test_focus` - focus()
- `test_blur` - blur()
- `test_click` - click()

**Complex Patterns (2 tests)**
- `test_create_and_insert` - Create + configure + insert
- `test_fragment_batch_insert` - DocumentFragment pattern

### Integration Tests (17 tests)

**Transpilation Parity (15 tests)**
- `test_todo_app_create_and_append` - Todo app pattern
- `test_form_input_value` - Form handling
- `test_dynamic_class_toggle` - Class manipulation
- `test_element_cloning` - Element cloning
- `test_dom_traversal_chain` - Chained traversal
- `test_query_and_modify` - Query + modify pattern
- `test_fragment_batch_append` - DocumentFragment
- `test_dataset_manipulation` - Data attributes
- `test_nested_queries` - Nested queries
- `test_svg_creation` - SVG namespace
- `test_no_py_runtime_in_output` - Zero runtime verification
- `test_clean_passthrough_output` - Clean JS output
- `test_complex_app_structure` - Complex app
- `test_list_rendering` - List rendering
- `test_conditional_display` - Conditional visibility

**Import Passthrough (2 tests)**
- `test_import_document_passthrough` - No import generated
- `test_import_element_type_only` - Type-only imports

## Key Assertions

All tests verify:

1. **Passthrough** - DOM APIs transpile unchanged
2. **No Runtime** - No `__py.*` wrappers for pure DOM code
3. **Clean Output** - Output matches hand-written JavaScript
4. **Correct Syntax** - Valid JavaScript generated

## Running Tests

```bash
# Run all Phase 34.1 tests
pytest tests/unit/client/test_341*.py tests/integration/transpiler/test_341_dom_parity.py -v

# Run specific category
pytest tests/unit/client/test_341_document.py -v
pytest tests/unit/client/test_341_element_attrs.py -v

# Run with coverage
pytest tests/unit/client/test_341*.py --cov=pynext.transpiler --cov-report=term-missing
```

## Coverage

| Module | Lines Covered |
|--------|---------------|
| `pynext/transpiler/dom.py` | 100% |
| `pynext/transpiler/imports.py` (DOM parts) | 100% |
| `pynext/transpiler/emitter.py` (DOM parts) | 95% |
| `pynext/client/dom.py` | 100% (stubs) |
| `pynext/client/node.py` | 100% (stubs) |

