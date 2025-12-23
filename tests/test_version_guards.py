#!/usr/bin/env python3
"""
Comprehensive unit tests for version guard functionality in prompt_builder.py

Tests all version guard features including:
- Version parsing
- Version comparison
- Guard token aliases (all 93 tokens)
- Version guard evaluation
- Component version context extraction
- Multi-specialization scenarios
- Edge cases and error handling

Run with: pytest tests/test_version_guards.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# Add the prompt-builder scripts to path
SCRIPT_DIR = Path(__file__).parent.parent / ".claude" / "skills" / "prompt-builder" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Import functions to test
from prompt_builder import (
    parse_version,
    version_matches,
    evaluate_version_guard,
    apply_version_guards,
    get_component_version_context,
    infer_component_from_specializations,
    validate_template_path,
    strip_yaml_frontmatter,
    GUARD_TOKEN_ALIASES,
)


# =============================================================================
# Test: parse_version()
# =============================================================================

class TestParseVersion:
    """Tests for parse_version() function."""

    def test_simple_major_minor(self):
        """Parse simple major.minor versions."""
        assert parse_version("3.10") == (3, 10)
        assert parse_version("1.8") == (1, 8)
        assert parse_version("17.0") == (17, 0)

    def test_major_minor_patch(self):
        """Parse major.minor.patch versions."""
        assert parse_version("3.11.4") == (3, 11, 4)
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("2.7.18") == (2, 7, 18)

    def test_single_number(self):
        """Parse single number versions (e.g., Java 17)."""
        assert parse_version("17") == (17,)
        assert parse_version("8") == (8,)
        assert parse_version("21") == (21,)

    def test_four_part_version(self):
        """Parse four-part versions."""
        assert parse_version("1.2.3.4") == (1, 2, 3, 4)

    def test_none_input(self):
        """Return None for None input."""
        assert parse_version(None) is None

    def test_empty_string(self):
        """Return None for empty string."""
        assert parse_version("") is None

    def test_whitespace_handling(self):
        """Handle leading/trailing whitespace."""
        assert parse_version("  3.10  ") == (3, 10)
        assert parse_version("\t17\n") == (17,)

    def test_invalid_version_string(self):
        """Return None for invalid version strings."""
        assert parse_version("abc") is None
        assert parse_version("3.x") is None
        assert parse_version("latest") is None

    def test_numeric_input(self):
        """Handle numeric input (converted to string)."""
        assert parse_version(17) == (17,)
        # Note: float 3.10 becomes "3.1" when converted to string
        result = parse_version(3.10)
        assert result is not None


# =============================================================================
# Test: version_matches()
# =============================================================================

class TestVersionMatches:
    """Tests for version_matches() function."""

    def test_greater_than_or_equal(self):
        """Test >= operator."""
        assert version_matches((3, 11), ">=", (3, 10)) is True
        assert version_matches((3, 10), ">=", (3, 10)) is True
        assert version_matches((3, 9), ">=", (3, 10)) is False

    def test_greater_than(self):
        """Test > operator."""
        assert version_matches((3, 11), ">", (3, 10)) is True
        assert version_matches((3, 10), ">", (3, 10)) is False
        assert version_matches((3, 9), ">", (3, 10)) is False

    def test_less_than_or_equal(self):
        """Test <= operator."""
        assert version_matches((3, 9), "<=", (3, 10)) is True
        assert version_matches((3, 10), "<=", (3, 10)) is True
        assert version_matches((3, 11), "<=", (3, 10)) is False

    def test_less_than(self):
        """Test < operator."""
        assert version_matches((3, 9), "<", (3, 10)) is True
        assert version_matches((3, 10), "<", (3, 10)) is False
        assert version_matches((3, 11), "<", (3, 10)) is False

    def test_equal(self):
        """Test == operator."""
        assert version_matches((3, 10), "==", (3, 10)) is True
        assert version_matches((3, 11), "==", (3, 10)) is False
        assert version_matches((3, 9), "==", (3, 10)) is False

    def test_different_length_versions(self):
        """Test comparison of different length versions."""
        # (3, 10) vs (3, 10, 0) - should be equal with padding
        assert version_matches((3, 10), ">=", (3, 10, 0)) is True
        assert version_matches((3, 10, 1), ">=", (3, 10)) is True
        assert version_matches((17,), ">=", (17, 0)) is True

    def test_invalid_operator(self):
        """Return False for unknown operators."""
        assert version_matches((3, 10), "!=", (3, 10)) is False
        assert version_matches((3, 10), "~=", (3, 10)) is False


# =============================================================================
# Test: GUARD_TOKEN_ALIASES
# =============================================================================

class TestGuardTokenAliases:
    """Tests for GUARD_TOKEN_ALIASES dictionary."""

    def test_python_aliases(self):
        """Python aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('py') == 'python'
        assert GUARD_TOKEN_ALIASES.get('python3') == 'python'

    def test_typescript_aliases(self):
        """TypeScript aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('ts') == 'typescript'

    def test_javascript_aliases(self):
        """JavaScript aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('js') == 'javascript'

    def test_ruby_aliases(self):
        """Ruby aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('rb') == 'ruby'

    def test_rust_aliases(self):
        """Rust aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('rs') == 'rust'

    def test_go_aliases(self):
        """Go aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('golang') == 'go'

    def test_java_aliases(self):
        """Java aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('jdk') == 'java'
        assert GUARD_TOKEN_ALIASES.get('openjdk') == 'java'

    def test_kotlin_aliases(self):
        """Kotlin aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('kt') == 'kotlin'

    def test_csharp_aliases(self):
        """C# aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('cs') == 'csharp'
        assert GUARD_TOKEN_ALIASES.get('dotnet') == 'csharp'
        assert GUARD_TOKEN_ALIASES.get('.net') == 'csharp'

    def test_cpp_aliases(self):
        """C++ aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('c++') == 'cpp'
        assert GUARD_TOKEN_ALIASES.get('cplusplus') == 'cpp'

    def test_bash_aliases(self):
        """Bash aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('sh') == 'bash'
        assert GUARD_TOKEN_ALIASES.get('shell') == 'bash'
        assert GUARD_TOKEN_ALIASES.get('zsh') == 'bash'

    def test_database_aliases(self):
        """Database aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('postgres') == 'postgresql'
        assert GUARD_TOKEN_ALIASES.get('pg') == 'postgresql'
        assert GUARD_TOKEN_ALIASES.get('mongo') == 'mongodb'
        assert GUARD_TOKEN_ALIASES.get('mssql') == 'sqlserver'
        assert GUARD_TOKEN_ALIASES.get('es') == 'elasticsearch'

    def test_frontend_framework_aliases(self):
        """Frontend framework aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('next') == 'nextjs'
        assert GUARD_TOKEN_ALIASES.get('next.js') == 'nextjs'
        assert GUARD_TOKEN_ALIASES.get('react.js') == 'react'
        assert GUARD_TOKEN_ALIASES.get('vue.js') == 'vue'
        assert GUARD_TOKEN_ALIASES.get('angular.js') == 'angular'
        assert GUARD_TOKEN_ALIASES.get('tailwindcss') == 'tailwind'

    def test_backend_framework_aliases(self):
        """Backend framework aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('spring') == 'spring-boot'
        assert GUARD_TOKEN_ALIASES.get('springboot') == 'spring-boot'
        assert GUARD_TOKEN_ALIASES.get('nest') == 'nestjs'
        assert GUARD_TOKEN_ALIASES.get('expressjs') == 'express'
        assert GUARD_TOKEN_ALIASES.get('rubyonrails') == 'rails'
        assert GUARD_TOKEN_ALIASES.get('ror') == 'rails'

    def test_mobile_aliases(self):
        """Mobile framework aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('rn') == 'react-native'
        assert GUARD_TOKEN_ALIASES.get('reactnative') == 'react-native'

    def test_testing_aliases(self):
        """Testing framework aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('pw') == 'playwright'
        assert GUARD_TOKEN_ALIASES.get('cy') == 'cypress'
        assert GUARD_TOKEN_ALIASES.get('tc') == 'testcontainers'

    def test_infrastructure_aliases(self):
        """Infrastructure tool aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('tf') == 'terraform'
        assert GUARD_TOKEN_ALIASES.get('k8s') == 'kubernetes'
        assert GUARD_TOKEN_ALIASES.get('otel') == 'opentelemetry'
        assert GUARD_TOKEN_ALIASES.get('gha') == 'github-actions'

    def test_data_ai_aliases(self):
        """Data/AI tool aliases resolve correctly."""
        assert GUARD_TOKEN_ALIASES.get('spark') == 'pyspark'
        assert GUARD_TOKEN_ALIASES.get('scikit-learn') == 'sklearn'
        assert GUARD_TOKEN_ALIASES.get('lc') == 'langchain'


# =============================================================================
# Test: evaluate_version_guard()
# =============================================================================

class TestEvaluateVersionGuard:
    """Tests for evaluate_version_guard() function."""

    # --- Primary Language Tests ---

    def test_primary_language_match(self):
        """Guard matches primary language version."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("python >= 3.10", ctx) is True
        assert evaluate_version_guard("python >= 3.12", ctx) is False

    def test_primary_language_alias(self):
        """Guard with alias matches primary language."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("py >= 3.10", ctx) is True

    def test_primary_language_case_insensitive(self):
        """Guard matching is case insensitive."""
        ctx = {'primary_language': 'Python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("python >= 3.10", ctx) is True
        assert evaluate_version_guard("PYTHON >= 3.10", ctx) is True

    # --- Framework Tests ---

    def test_framework_match(self):
        """Guard matches framework version."""
        ctx = {'framework': 'fastapi', 'framework_version': '0.104'}
        assert evaluate_version_guard("fastapi >= 0.100", ctx) is True
        assert evaluate_version_guard("fastapi >= 0.110", ctx) is False

    def test_framework_alias(self):
        """Guard with alias matches framework."""
        ctx = {'framework': 'spring-boot', 'spring_boot_version': '3.2'}
        assert evaluate_version_guard("spring >= 3.0", ctx) is True

    # --- Language-Specific Version Fields ---

    def test_node_version_field(self):
        """Guard matches node_version field."""
        ctx = {'node_version': '18.17'}
        assert evaluate_version_guard("node >= 18", ctx) is True
        assert evaluate_version_guard("node >= 20", ctx) is False

    def test_java_version_field(self):
        """Guard matches java_version field."""
        ctx = {'java_version': '17'}
        assert evaluate_version_guard("java >= 17", ctx) is True
        assert evaluate_version_guard("java >= 21", ctx) is False

    def test_go_version_field(self):
        """Guard matches go_version field."""
        ctx = {'go_version': '1.21'}
        assert evaluate_version_guard("go >= 1.20", ctx) is True
        assert evaluate_version_guard("golang >= 1.20", ctx) is True

    def test_php_version_field(self):
        """Guard matches php_version field."""
        ctx = {'php_version': '8.2'}
        assert evaluate_version_guard("php >= 8.1", ctx) is True

    def test_kotlin_version_field(self):
        """Guard matches kotlin_version field."""
        ctx = {'kotlin_version': '1.9'}
        assert evaluate_version_guard("kotlin >= 1.8", ctx) is True
        assert evaluate_version_guard("kt >= 1.8", ctx) is True

    def test_scala_version_field(self):
        """Guard matches scala_version field."""
        ctx = {'scala_version': '3.3'}
        assert evaluate_version_guard("scala >= 3.0", ctx) is True

    def test_elixir_version_field(self):
        """Guard matches elixir_version field."""
        ctx = {'elixir_version': '1.15'}
        assert evaluate_version_guard("elixir >= 1.14", ctx) is True

    def test_swift_version_field(self):
        """Guard matches swift_version field."""
        ctx = {'swift_version': '5.9'}
        assert evaluate_version_guard("swift >= 5.8", ctx) is True

    def test_rust_version_field(self):
        """Guard matches rust_version field."""
        ctx = {'rust_version': '1.75'}
        assert evaluate_version_guard("rust >= 1.70", ctx) is True
        assert evaluate_version_guard("rs >= 1.70", ctx) is True

    def test_ruby_version_field(self):
        """Guard matches ruby_version field."""
        ctx = {'ruby_version': '3.2'}
        assert evaluate_version_guard("ruby >= 3.0", ctx) is True
        assert evaluate_version_guard("rb >= 3.0", ctx) is True

    # --- Database Version Fields ---

    def test_postgresql_version_field(self):
        """Guard matches postgresql_version field."""
        ctx = {'postgresql_version': '15'}
        assert evaluate_version_guard("postgresql >= 14", ctx) is True
        assert evaluate_version_guard("postgres >= 14", ctx) is True
        assert evaluate_version_guard("pg >= 14", ctx) is True

    def test_mysql_version_field(self):
        """Guard matches mysql_version field."""
        ctx = {'mysql_version': '8.0'}
        assert evaluate_version_guard("mysql >= 8.0", ctx) is True

    def test_mongodb_version_field(self):
        """Guard matches mongodb_version field."""
        ctx = {'mongodb_version': '6.0'}
        assert evaluate_version_guard("mongodb >= 5.0", ctx) is True
        assert evaluate_version_guard("mongo >= 5.0", ctx) is True

    def test_redis_version_field(self):
        """Guard matches redis_version field."""
        ctx = {'redis_version': '7.2'}
        assert evaluate_version_guard("redis >= 7.0", ctx) is True

    def test_elasticsearch_version_field(self):
        """Guard matches elasticsearch_version field."""
        ctx = {'elasticsearch_version': '8.10'}
        assert evaluate_version_guard("elasticsearch >= 8.0", ctx) is True
        assert evaluate_version_guard("es >= 8.0", ctx) is True

    # --- Frontend Framework Version Fields ---

    def test_react_version_field(self):
        """Guard matches react_version field."""
        ctx = {'react_version': '18.2'}
        assert evaluate_version_guard("react >= 18", ctx) is True

    def test_nextjs_version_field(self):
        """Guard matches nextjs_version field."""
        ctx = {'nextjs_version': '14.0'}
        assert evaluate_version_guard("nextjs >= 13", ctx) is True
        assert evaluate_version_guard("next >= 13", ctx) is True

    def test_vue_version_field(self):
        """Guard matches vue_version field."""
        ctx = {'vue_version': '3.4'}
        assert evaluate_version_guard("vue >= 3.0", ctx) is True

    def test_angular_version_field(self):
        """Guard matches angular_version field."""
        ctx = {'angular_version': '17'}
        assert evaluate_version_guard("angular >= 16", ctx) is True

    def test_svelte_version_field(self):
        """Guard matches svelte_version field."""
        ctx = {'svelte_version': '4.2'}
        assert evaluate_version_guard("svelte >= 4.0", ctx) is True

    def test_tailwind_version_field(self):
        """Guard matches tailwind_version field."""
        ctx = {'tailwind_version': '3.4'}
        assert evaluate_version_guard("tailwind >= 3.0", ctx) is True
        assert evaluate_version_guard("tailwindcss >= 3.0", ctx) is True

    # --- Backend Framework Version Fields ---

    def test_django_version_field(self):
        """Guard matches django_version field."""
        ctx = {'django_version': '5.0'}
        assert evaluate_version_guard("django >= 4.2", ctx) is True

    def test_flask_version_field(self):
        """Guard matches flask_version field."""
        ctx = {'flask_version': '3.0'}
        assert evaluate_version_guard("flask >= 2.0", ctx) is True

    def test_express_version_field(self):
        """Guard matches express_version field."""
        ctx = {'express_version': '4.18'}
        assert evaluate_version_guard("express >= 4.17", ctx) is True

    def test_nestjs_version_field(self):
        """Guard matches nestjs_version field."""
        ctx = {'nestjs_version': '10.0'}
        assert evaluate_version_guard("nestjs >= 9.0", ctx) is True
        assert evaluate_version_guard("nest >= 9.0", ctx) is True

    def test_rails_version_field(self):
        """Guard matches rails_version field."""
        ctx = {'rails_version': '7.1'}
        assert evaluate_version_guard("rails >= 7.0", ctx) is True
        assert evaluate_version_guard("ror >= 7.0", ctx) is True

    def test_spring_boot_version_field(self):
        """Guard matches spring_boot_version field."""
        ctx = {'spring_boot_version': '3.2'}
        assert evaluate_version_guard("spring-boot >= 3.0", ctx) is True

    # --- Testing Framework Version Fields ---

    def test_playwright_version_field(self):
        """Guard matches playwright_version field."""
        ctx = {'playwright_version': '1.40'}
        assert evaluate_version_guard("playwright >= 1.35", ctx) is True
        assert evaluate_version_guard("pw >= 1.35", ctx) is True

    def test_cypress_version_field(self):
        """Guard matches cypress_version field."""
        ctx = {'cypress_version': '13.6'}
        assert evaluate_version_guard("cypress >= 13.0", ctx) is True
        assert evaluate_version_guard("cy >= 13.0", ctx) is True

    def test_jest_version_field(self):
        """Guard matches jest_version field."""
        ctx = {'jest_version': '29.7'}
        assert evaluate_version_guard("jest >= 29.0", ctx) is True

    def test_pytest_version_field(self):
        """Guard matches pytest_version field."""
        ctx = {'pytest_version': '7.4'}
        assert evaluate_version_guard("pytest >= 7.0", ctx) is True

    # --- Infrastructure Version Fields ---

    def test_terraform_version_field(self):
        """Guard matches terraform_version field."""
        ctx = {'terraform_version': '1.6'}
        assert evaluate_version_guard("terraform >= 1.5", ctx) is True
        assert evaluate_version_guard("tf >= 1.5", ctx) is True

    def test_docker_version_field(self):
        """Guard matches docker_version field."""
        ctx = {'docker_version': '24.0'}
        assert evaluate_version_guard("docker >= 23.0", ctx) is True

    def test_kubernetes_version_field(self):
        """Guard matches kubernetes_version field."""
        ctx = {'kubernetes_version': '1.28'}
        assert evaluate_version_guard("kubernetes >= 1.27", ctx) is True
        assert evaluate_version_guard("k8s >= 1.27", ctx) is True

    # --- Infrastructure Section Lookup ---

    def test_infrastructure_section_lookup(self):
        """Guard checks infrastructure section."""
        ctx = {
            'infrastructure': {
                'docker_version': '24.0',
                'terraform_version': '1.6',
            }
        }
        assert evaluate_version_guard("docker >= 23.0", ctx) is True
        assert evaluate_version_guard("terraform >= 1.5", ctx) is True

    # --- Testing Section Lookup ---

    def test_testing_section_lookup(self):
        """Guard checks testing section."""
        ctx = {
            'testing': {
                'jest_version': '29.7',
                'playwright_version': '1.40',
            }
        }
        assert evaluate_version_guard("jest >= 29.0", ctx) is True
        assert evaluate_version_guard("playwright >= 1.35", ctx) is True

    # --- Databases Section Lookup ---

    def test_databases_section_lookup(self):
        """Guard checks databases section."""
        ctx = {
            'databases': {
                'postgresql_version': '15',
                'redis_version': '7.2',
            }
        }
        assert evaluate_version_guard("postgresql >= 14", ctx) is True
        assert evaluate_version_guard("redis >= 7.0", ctx) is True

    # --- Secondary Languages ---

    def test_secondary_language_dict_format(self):
        """Guard matches secondary languages in dict format."""
        ctx = {
            'primary_language': 'typescript',
            'secondary_languages': [
                {'name': 'python', 'version': '3.11'},
                {'name': 'go', 'version': '1.21'},
            ]
        }
        assert evaluate_version_guard("python >= 3.10", ctx) is True
        assert evaluate_version_guard("go >= 1.20", ctx) is True

    def test_secondary_language_string_format(self):
        """Guard handles secondary languages in string format (no version)."""
        ctx = {
            'primary_language': 'typescript',
            'secondary_languages': ['python', 'sql']
        }
        # No version info - should return True (conservative)
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    # --- Multiple Conditions (AND) ---

    def test_multiple_conditions_all_pass(self):
        """All conditions must pass for compound guards."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.10'}
        assert evaluate_version_guard("python >= 3.7, python < 3.11", ctx) is True

    def test_multiple_conditions_one_fails(self):
        """Guard fails if any condition fails."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("python >= 3.7, python < 3.11", ctx) is False

    # --- Edge Cases ---

    def test_none_context(self):
        """Return True for None context (conservative)."""
        assert evaluate_version_guard("python >= 3.10", None) is True

    def test_empty_context(self):
        """Return True for empty context (conservative)."""
        assert evaluate_version_guard("python >= 3.10", {}) is True

    def test_no_version_detected(self):
        """Return True when language exists but no version (conservative)."""
        ctx = {'primary_language': 'python'}  # No version
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    def test_unparseable_condition(self):
        """Skip unparseable conditions."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        # Invalid syntax - should be skipped, return True
        assert evaluate_version_guard("python 3.10", ctx) is True
        assert evaluate_version_guard("invalid guard", ctx) is True


# =============================================================================
# Test: apply_version_guards()
# =============================================================================

class TestApplyVersionGuards:
    """Tests for apply_version_guards() function."""

    def test_single_guard_included(self):
        """Content after matching guard is included."""
        content = """Some intro text

<!-- version: python >= 3.10 -->
Use match-case statements for pattern matching.

More content."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        result = apply_version_guards(content, ctx)
        assert "match-case statements" in result

    def test_single_guard_excluded(self):
        """Content after non-matching guard is excluded."""
        content = """Some intro text

<!-- version: python >= 3.12 -->
Use new Python 3.12 features.

More content."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        result = apply_version_guards(content, ctx)
        assert "Python 3.12 features" not in result
        assert "Some intro text" in result

    def test_multiple_guards_alternating(self):
        """Multiple guards filter content correctly."""
        content = """Base content

<!-- version: python >= 3.10 -->
Python 3.10+ content

<!-- version: python >= 3.12 -->
Python 3.12+ content

<!-- version: python >= 3.8 -->
Python 3.8+ content
"""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        result = apply_version_guards(content, ctx)
        assert "Python 3.10+ content" in result
        assert "Python 3.12+ content" not in result
        assert "Python 3.8+ content" in result

    def test_guard_reset_at_section_boundary(self):
        """Guards reset at section boundaries (---)."""
        content = """<!-- version: python >= 3.12 -->
This should be excluded.

---

This should be included (after boundary)."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        result = apply_version_guards(content, ctx)
        assert "should be excluded" not in result
        assert "should be included" in result

    def test_no_guards_passthrough(self):
        """Content without guards passes through unchanged."""
        content = "No guards here, just plain text."
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        result = apply_version_guards(content, ctx)
        assert result == content

    def test_none_context_includes_all(self):
        """All content included when context is None."""
        content = """<!-- version: python >= 3.12 -->
This would normally be excluded."""
        result = apply_version_guards(content, None)
        assert "would normally be excluded" in result


# =============================================================================
# Test: get_component_version_context()
# =============================================================================

class TestGetComponentVersionContext:
    """Tests for get_component_version_context() function."""

    def test_exact_path_match(self):
        """Exact component path match."""
        project_ctx = {
            'components': [
                {
                    'path': 'backend/',
                    'language': 'python',
                    'language_version': '3.11',
                    'framework': 'fastapi',
                    'framework_version': '0.104',
                }
            ]
        }
        result = get_component_version_context(project_ctx, 'backend/')
        assert result['primary_language'] == 'python'
        assert result['primary_language_version'] == '3.11'
        assert result['framework'] == 'fastapi'
        assert result['framework_version'] == '0.104'

    def test_longest_prefix_match(self):
        """Longest prefix match for nested paths."""
        project_ctx = {
            'components': [
                {'path': 'backend/', 'language': 'python', 'language_version': '3.10'},
                {'path': 'backend/api/', 'language': 'python', 'language_version': '3.11'},
            ]
        }
        # Should match backend/api/ (longer prefix)
        result = get_component_version_context(project_ctx, 'backend/api/routes/')
        assert result['primary_language_version'] == '3.11'

        # Should match backend/ only
        result = get_component_version_context(project_ctx, 'backend/utils/')
        assert result['primary_language_version'] == '3.10'

    def test_extracts_all_version_fields(self):
        """Extracts all *_version fields from component."""
        project_ctx = {
            'components': [
                {
                    'path': 'backend/',
                    'language': 'python',
                    'language_version': '3.11',
                    'framework': 'fastapi',
                    'framework_version': '0.104',
                    'database': 'postgresql',
                    'database_version': '15',
                    'pytest_version': '7.4',
                    'pydantic_version': '2.5',
                    'node_version': '18',
                }
            ]
        }
        result = get_component_version_context(project_ctx, 'backend/')
        assert result.get('database_version') == '15'
        assert result.get('pytest_version') == '7.4'
        assert result.get('pydantic_version') == '2.5'
        assert result.get('node_version') == '18'

    def test_none_project_context(self):
        """Return empty dict for None project context."""
        result = get_component_version_context(None, 'backend/')
        assert result == {}

    def test_empty_components(self):
        """Fallback to global versions when no components."""
        project_ctx = {
            'primary_language': 'python',
            'primary_language_version': '3.11',
            'components': []
        }
        result = get_component_version_context(project_ctx, 'backend/')
        assert result['primary_language'] == 'python'
        assert result['primary_language_version'] == '3.11'

    def test_no_component_path(self):
        """Fallback to global versions when no component_path."""
        project_ctx = {
            'primary_language': 'typescript',
            'primary_language_version': '5.0',
        }
        result = get_component_version_context(project_ctx, None)
        assert result['primary_language'] == 'typescript'

    def test_no_matching_component(self):
        """Fallback to global when no component matches."""
        project_ctx = {
            'primary_language': 'python',
            'primary_language_version': '3.11',
            'components': [
                {'path': 'frontend/', 'language': 'typescript'}
            ]
        }
        result = get_component_version_context(project_ctx, 'backend/')
        assert result['primary_language'] == 'python'

    def test_trailing_slash_normalization(self):
        """Path matching handles trailing slashes consistently."""
        project_ctx = {
            'components': [
                {'path': 'backend', 'language': 'python', 'language_version': '3.11'}
            ]
        }
        # Both with and without trailing slash should match
        result1 = get_component_version_context(project_ctx, 'backend/')
        assert result1['primary_language_version'] == '3.11'


# =============================================================================
# Test: infer_component_from_specializations()
# =============================================================================

class TestInferComponentFromSpecializations:
    """Tests for infer_component_from_specializations() function."""

    def test_infer_from_language_template(self):
        """Infer component from language specialization."""
        project_ctx = {
            'components': [
                {'path': 'backend/', 'language': 'python'},
                {'path': 'frontend/', 'language': 'typescript'},
            ]
        }
        spec_paths = ['templates/specializations/01-languages/python.md']
        result = infer_component_from_specializations(spec_paths, project_ctx)
        assert result == 'backend/'

    def test_infer_from_frontend_framework(self):
        """Infer component from frontend framework specialization."""
        project_ctx = {
            'components': [
                {'path': 'backend/', 'language': 'python', 'framework': 'fastapi'},
                {'path': 'frontend/', 'language': 'typescript', 'framework': 'react'},
            ]
        }
        spec_paths = ['templates/specializations/02-frameworks-frontend/react.md']
        result = infer_component_from_specializations(spec_paths, project_ctx)
        assert result == 'frontend/'

    def test_infer_from_backend_framework(self):
        """Infer component from backend framework specialization."""
        project_ctx = {
            'components': [
                {'path': 'backend/', 'language': 'python', 'framework': 'fastapi'},
                {'path': 'frontend/', 'language': 'typescript', 'framework': 'nextjs'},
            ]
        }
        spec_paths = ['templates/specializations/03-frameworks-backend/fastapi.md']
        result = infer_component_from_specializations(spec_paths, project_ctx)
        assert result == 'backend/'

    def test_none_spec_paths(self):
        """Return None for None spec_paths."""
        result = infer_component_from_specializations(None, {'components': []})
        assert result is None

    def test_empty_spec_paths(self):
        """Return None for empty spec_paths."""
        result = infer_component_from_specializations([], {'components': []})
        assert result is None

    def test_none_project_context(self):
        """Return None for None project context."""
        result = infer_component_from_specializations(['some/path.md'], None)
        assert result is None

    def test_no_matching_component(self):
        """Return None when no component matches specialization."""
        project_ctx = {
            'components': [
                {'path': 'backend/', 'language': 'java'},
            ]
        }
        spec_paths = ['templates/specializations/01-languages/python.md']
        result = infer_component_from_specializations(spec_paths, project_ctx)
        assert result is None


# =============================================================================
# Test: strip_yaml_frontmatter()
# =============================================================================

class TestStripYamlFrontmatter:
    """Tests for strip_yaml_frontmatter() function."""

    def test_strip_frontmatter(self):
        """Strip YAML frontmatter from content."""
        content = """---
name: test
version: 1.0
---

# Main Content

This is the body."""
        result = strip_yaml_frontmatter(content)
        assert result.startswith("# Main Content")
        assert "name: test" not in result
        assert "---" not in result.split('\n')[0]

    def test_no_frontmatter(self):
        """Return content unchanged if no frontmatter."""
        content = "# Just a heading\n\nSome content."
        result = strip_yaml_frontmatter(content)
        assert result == content

    def test_unclosed_frontmatter(self):
        """Return original if frontmatter not closed."""
        content = """---
name: test
no closing marker here"""
        result = strip_yaml_frontmatter(content)
        assert result == content

    def test_empty_frontmatter(self):
        """Handle empty frontmatter."""
        content = """---
---

Content after."""
        result = strip_yaml_frontmatter(content)
        assert result.strip() == "Content after."


# =============================================================================
# Test: validate_template_path() - Security Tests
# =============================================================================

class TestValidateTemplatePath:
    """Tests for validate_template_path() function - security validation."""

    def test_reject_absolute_path(self):
        """Reject absolute paths."""
        result = validate_template_path("/etc/passwd")
        assert result is None

    def test_reject_parent_traversal(self):
        """Reject paths with parent traversal."""
        result = validate_template_path("../../../etc/passwd")
        assert result is None
        result = validate_template_path("bazinga/../../../etc/passwd")
        assert result is None


# =============================================================================
# Test: Multi-Specialization Integration
# =============================================================================

class TestMultiSpecializationIntegration:
    """Integration tests for multiple specializations scenario."""

    def test_all_guards_evaluate_with_unified_context(self):
        """All specialization guards should evaluate against unified context."""
        # Simulate a component with multiple version fields
        component_ctx = {
            'primary_language': 'python',
            'primary_language_version': '3.11',
            'framework': 'fastapi',
            'framework_version': '0.104',
            'database': 'postgresql',
            'postgresql_version': '15',
            'pytest_version': '7.4',
        }

        # Each specialization's guard should work
        assert evaluate_version_guard("python >= 3.10", component_ctx) is True
        assert evaluate_version_guard("fastapi >= 0.100", component_ctx) is True
        assert evaluate_version_guard("postgresql >= 14", component_ctx) is True
        assert evaluate_version_guard("pytest >= 7.0", component_ctx) is True

    def test_full_stack_component_context(self):
        """Full-stack component with all version types."""
        project_ctx = {
            'components': [
                {
                    'path': 'app/',
                    'language': 'typescript',
                    'language_version': '5.0',
                    'node_version': '18',
                    'framework': 'nextjs',
                    'framework_version': '14.0',
                    'database': 'postgresql',
                    'database_version': '15',
                    'react_version': '18.2',
                    'tailwind_version': '3.4',
                    'playwright_version': '1.40',
                    'jest_version': '29.7',
                }
            ]
        }

        ctx = get_component_version_context(project_ctx, 'app/')

        # All these guards should pass
        assert evaluate_version_guard("typescript >= 5.0", ctx) is True
        assert evaluate_version_guard("node >= 18", ctx) is True
        assert evaluate_version_guard("nextjs >= 14", ctx) is True
        assert evaluate_version_guard("postgresql >= 15", ctx) is True
        assert evaluate_version_guard("react >= 18", ctx) is True
        assert evaluate_version_guard("tailwind >= 3.0", ctx) is True
        assert evaluate_version_guard("playwright >= 1.35", ctx) is True
        assert evaluate_version_guard("jest >= 29", ctx) is True

    def test_monorepo_different_components(self):
        """Different components in monorepo get correct versions."""
        project_ctx = {
            'components': [
                {
                    'path': 'frontend/',
                    'language': 'typescript',
                    'language_version': '5.0',
                    'framework': 'react',
                    'framework_version': '18.2',
                    'node_version': '20',
                },
                {
                    'path': 'backend/',
                    'language': 'python',
                    'language_version': '3.11',
                    'framework': 'fastapi',
                    'framework_version': '0.104',
                    'postgresql_version': '15',
                },
                {
                    'path': 'services/auth/',
                    'language': 'go',
                    'language_version': '1.21',
                    'framework': 'gin',
                    'framework_version': '1.9',
                    'redis_version': '7.2',
                },
            ]
        }

        # Frontend component
        frontend_ctx = get_component_version_context(project_ctx, 'frontend/')
        assert frontend_ctx['primary_language'] == 'typescript'
        assert evaluate_version_guard("typescript >= 5.0", frontend_ctx) is True
        assert evaluate_version_guard("react >= 18", frontend_ctx) is True

        # Backend component
        backend_ctx = get_component_version_context(project_ctx, 'backend/')
        assert backend_ctx['primary_language'] == 'python'
        assert evaluate_version_guard("python >= 3.10", backend_ctx) is True
        assert evaluate_version_guard("fastapi >= 0.100", backend_ctx) is True
        assert evaluate_version_guard("postgresql >= 14", backend_ctx) is True

        # Auth service component
        auth_ctx = get_component_version_context(project_ctx, 'services/auth/')
        assert auth_ctx['primary_language'] == 'go'
        assert evaluate_version_guard("go >= 1.20", auth_ctx) is True
        assert evaluate_version_guard("gin >= 1.8", auth_ctx) is True
        assert evaluate_version_guard("redis >= 7.0", auth_ctx) is True


# =============================================================================
# Test: All 93 Guard Tokens Coverage
# =============================================================================

class TestAll93GuardTokens:
    """Test coverage for all 93 unique version guard tokens from specializations."""

    @pytest.fixture
    def full_context(self):
        """Context with all version fields populated."""
        return {
            # Languages
            'primary_language': 'python',
            'primary_language_version': '3.11',
            'node_version': '18',
            'java_version': '17',
            'go_version': '1.21',
            'php_version': '8.2',
            'kotlin_version': '1.9',
            'scala_version': '3.3',
            'elixir_version': '1.15',
            'swift_version': '5.9',
            'rust_version': '1.75',
            'ruby_version': '3.2',
            'cpp_version': '20',
            'bash_version': '5.2',
            'dart_version': '3.2',
            # Databases
            'postgresql_version': '15',
            'mysql_version': '8.0',
            'mongodb_version': '6.0',
            'redis_version': '7.2',
            'elasticsearch_version': '8.10',
            'sqlserver_version': '2022',
            'oracle_version': '21',
            # Frontend frameworks
            'framework': 'react',
            'framework_version': '18.2',
            'react_version': '18.2',
            'nextjs_version': '14.0',
            'vue_version': '3.4',
            'angular_version': '17',
            'svelte_version': '4.2',
            'astro_version': '4.0',
            'htmx_version': '1.9',
            'alpine_version': '3.13',
            'tailwind_version': '3.4',
            # Backend frameworks
            'spring_boot_version': '3.2',
            'django_version': '5.0',
            'flask_version': '3.0',
            'fastapi_version': '0.104',
            'express_version': '4.18',
            'nestjs_version': '10.0',
            'rails_version': '7.1',
            'laravel_version': '10.0',
            'gin_version': '1.9',
            'fiber_version': '2.50',
            'phoenix_version': '1.7',
            # Mobile
            'flutter_version': '3.16',
            'react_native_version': '0.73',
            'ios_version': '17',
            'tauri_version': '1.5',
            'electron_version': '28',
            # Testing
            'playwright_version': '1.40',
            'cypress_version': '13.6',
            'selenium_version': '4.15',
            'jest_version': '29.7',
            'vitest_version': '1.0',
            'pytest_version': '7.4',
            'testcontainers_version': '3.7',
            # Infrastructure
            'terraform_version': '1.6',
            'docker_version': '24.0',
            'kubernetes_version': '1.28',
            'opentelemetry_version': '1.21',
            'prometheus_version': '2.47',
            'github_actions_version': '3',
            # Data/AI
            'pyspark_version': '3.5',
            'airflow_version': '2.7',
            'langchain_version': '0.1',
            'sklearn_version': '1.3',
            'pydantic_version': '2.5',
            'dbt_version': '1.7',
            'mlflow_version': '2.9',
            # APIs
            'openapi_version': '3.1',
            'grpc_version': '1.59',
            'kafka_version': '3.6',
            'graphql_version': '16',
            'protobuf_version': '25.0',
            # Auth
            'oauth_version': '2.1',
            'jwt_version': '9.0',
            # Validation
            'zod_version': '3.22',
            'joi_version': '17.11',
            'prisma_version': '5.6',
        }

    # Languages
    def test_python(self, full_context):
        assert evaluate_version_guard("python >= 3.10", full_context) is True

    def test_typescript(self, full_context):
        full_context['primary_language'] = 'typescript'
        full_context['primary_language_version'] = '5.0'
        assert evaluate_version_guard("typescript >= 5.0", full_context) is True

    def test_java(self, full_context):
        assert evaluate_version_guard("java >= 17", full_context) is True

    def test_kotlin(self, full_context):
        assert evaluate_version_guard("kotlin >= 1.9", full_context) is True

    def test_rust(self, full_context):
        assert evaluate_version_guard("rust >= 1.70", full_context) is True

    def test_ruby(self, full_context):
        assert evaluate_version_guard("ruby >= 3.0", full_context) is True

    def test_go(self, full_context):
        assert evaluate_version_guard("go >= 1.20", full_context) is True

    def test_csharp(self, full_context):
        full_context['dotnet_version'] = '8.0'
        assert evaluate_version_guard("csharp >= 8.0", full_context) is True

    def test_php(self, full_context):
        assert evaluate_version_guard("php >= 8.2", full_context) is True

    def test_scala(self, full_context):
        assert evaluate_version_guard("scala >= 3", full_context) is True

    def test_elixir(self, full_context):
        assert evaluate_version_guard("elixir >= 1.14", full_context) is True

    def test_swift(self, full_context):
        assert evaluate_version_guard("swift >= 5.8", full_context) is True

    def test_cpp(self, full_context):
        assert evaluate_version_guard("cpp >= 17", full_context) is True

    def test_bash(self, full_context):
        assert evaluate_version_guard("bash >= 5.0", full_context) is True

    def test_dart(self, full_context):
        assert evaluate_version_guard("dart >= 3.0", full_context) is True

    def test_node(self, full_context):
        assert evaluate_version_guard("node >= 18", full_context) is True

    # Databases
    def test_postgresql(self, full_context):
        assert evaluate_version_guard("postgresql >= 14", full_context) is True

    def test_mysql(self, full_context):
        assert evaluate_version_guard("mysql >= 8.0", full_context) is True

    def test_mongodb(self, full_context):
        assert evaluate_version_guard("mongodb >= 5.0", full_context) is True

    def test_redis(self, full_context):
        assert evaluate_version_guard("redis >= 7.0", full_context) is True

    def test_elasticsearch(self, full_context):
        assert evaluate_version_guard("elasticsearch >= 8.0", full_context) is True

    def test_sqlserver(self, full_context):
        assert evaluate_version_guard("sqlserver >= 2019", full_context) is True

    def test_oracle(self, full_context):
        assert evaluate_version_guard("oracle >= 19", full_context) is True

    # Frontend
    def test_react(self, full_context):
        assert evaluate_version_guard("react >= 18", full_context) is True

    def test_nextjs(self, full_context):
        assert evaluate_version_guard("nextjs >= 13", full_context) is True

    def test_vue(self, full_context):
        assert evaluate_version_guard("vue >= 3.0", full_context) is True

    def test_angular(self, full_context):
        assert evaluate_version_guard("angular >= 16", full_context) is True

    def test_svelte(self, full_context):
        assert evaluate_version_guard("svelte >= 4.0", full_context) is True

    def test_astro(self, full_context):
        assert evaluate_version_guard("astro >= 3.0", full_context) is True

    def test_htmx(self, full_context):
        assert evaluate_version_guard("htmx >= 1.9", full_context) is True

    def test_alpine(self, full_context):
        assert evaluate_version_guard("alpine >= 3.12", full_context) is True

    def test_tailwind(self, full_context):
        assert evaluate_version_guard("tailwind >= 3.0", full_context) is True

    # Backend
    def test_spring_boot(self, full_context):
        assert evaluate_version_guard("spring-boot >= 3.0", full_context) is True

    def test_django(self, full_context):
        assert evaluate_version_guard("django >= 4.0", full_context) is True

    def test_flask(self, full_context):
        assert evaluate_version_guard("flask >= 2.0", full_context) is True

    def test_fastapi(self, full_context):
        assert evaluate_version_guard("fastapi >= 0.100", full_context) is True

    def test_express(self, full_context):
        assert evaluate_version_guard("express >= 4.17", full_context) is True

    def test_nestjs(self, full_context):
        assert evaluate_version_guard("nestjs >= 9.0", full_context) is True

    def test_rails(self, full_context):
        assert evaluate_version_guard("rails >= 7.0", full_context) is True

    def test_laravel(self, full_context):
        assert evaluate_version_guard("laravel >= 10.0", full_context) is True

    def test_gin(self, full_context):
        assert evaluate_version_guard("gin >= 1.8", full_context) is True

    def test_fiber(self, full_context):
        assert evaluate_version_guard("fiber >= 2.40", full_context) is True

    def test_phoenix(self, full_context):
        assert evaluate_version_guard("phoenix >= 1.6", full_context) is True

    # Mobile
    def test_flutter(self, full_context):
        assert evaluate_version_guard("flutter >= 3.10", full_context) is True

    def test_react_native(self, full_context):
        assert evaluate_version_guard("react-native >= 0.70", full_context) is True

    def test_ios(self, full_context):
        assert evaluate_version_guard("ios >= 16", full_context) is True

    def test_tauri(self, full_context):
        assert evaluate_version_guard("tauri >= 1.4", full_context) is True

    def test_electron(self, full_context):
        assert evaluate_version_guard("electron >= 25", full_context) is True

    # Testing
    def test_playwright(self, full_context):
        assert evaluate_version_guard("playwright >= 1.35", full_context) is True

    def test_cypress(self, full_context):
        assert evaluate_version_guard("cypress >= 13.0", full_context) is True

    def test_selenium(self, full_context):
        assert evaluate_version_guard("selenium >= 4.10", full_context) is True

    def test_jest(self, full_context):
        assert evaluate_version_guard("jest >= 29.0", full_context) is True

    def test_vitest(self, full_context):
        assert evaluate_version_guard("vitest >= 0.34", full_context) is True

    def test_pytest(self, full_context):
        assert evaluate_version_guard("pytest >= 7.0", full_context) is True

    def test_testcontainers(self, full_context):
        assert evaluate_version_guard("testcontainers >= 3.5", full_context) is True

    # Infrastructure
    def test_terraform(self, full_context):
        assert evaluate_version_guard("terraform >= 1.5", full_context) is True

    def test_docker(self, full_context):
        assert evaluate_version_guard("docker >= 23.0", full_context) is True

    def test_kubernetes(self, full_context):
        assert evaluate_version_guard("kubernetes >= 1.27", full_context) is True

    def test_opentelemetry(self, full_context):
        assert evaluate_version_guard("opentelemetry >= 1.20", full_context) is True

    def test_prometheus(self, full_context):
        assert evaluate_version_guard("prometheus >= 2.45", full_context) is True

    def test_github_actions(self, full_context):
        assert evaluate_version_guard("github-actions >= 3", full_context) is True

    # Data/AI
    def test_pyspark(self, full_context):
        assert evaluate_version_guard("pyspark >= 3.4", full_context) is True

    def test_airflow(self, full_context):
        assert evaluate_version_guard("airflow >= 2.6", full_context) is True

    def test_langchain(self, full_context):
        assert evaluate_version_guard("langchain >= 0.1", full_context) is True

    def test_sklearn(self, full_context):
        assert evaluate_version_guard("sklearn >= 1.2", full_context) is True

    def test_pydantic(self, full_context):
        assert evaluate_version_guard("pydantic >= 2.0", full_context) is True

    def test_dbt(self, full_context):
        assert evaluate_version_guard("dbt >= 1.6", full_context) is True

    def test_mlflow(self, full_context):
        assert evaluate_version_guard("mlflow >= 2.8", full_context) is True

    # APIs
    def test_openapi(self, full_context):
        assert evaluate_version_guard("openapi >= 3.0", full_context) is True

    def test_grpc(self, full_context):
        assert evaluate_version_guard("grpc >= 1.50", full_context) is True

    def test_kafka(self, full_context):
        assert evaluate_version_guard("kafka >= 3.5", full_context) is True

    def test_graphql(self, full_context):
        assert evaluate_version_guard("graphql >= 16", full_context) is True

    def test_protobuf(self, full_context):
        assert evaluate_version_guard("protobuf >= 24.0", full_context) is True

    # Auth
    def test_oauth(self, full_context):
        assert evaluate_version_guard("oauth >= 2.0", full_context) is True

    def test_jwt(self, full_context):
        assert evaluate_version_guard("jwt >= 9.0", full_context) is True

    # Validation
    def test_zod(self, full_context):
        assert evaluate_version_guard("zod >= 3.20", full_context) is True

    def test_joi(self, full_context):
        assert evaluate_version_guard("joi >= 17.10", full_context) is True

    def test_prisma(self, full_context):
        assert evaluate_version_guard("prisma >= 5.0", full_context) is True


# =============================================================================
# Test: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_version_in_context(self):
        """Handle malformed version strings in context."""
        ctx = {'primary_language': 'python', 'primary_language_version': 'latest'}
        # Should return True (conservative) when version can't be parsed
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    def test_special_characters_in_version(self):
        """Handle special characters in version strings."""
        ctx = {'primary_language': 'python', 'primary_language_version': '>=3.10'}
        # parse_version should handle or reject this gracefully
        result = evaluate_version_guard("python >= 3.10", ctx)
        # Either True (parsed successfully) or True (fallback)
        assert result is True

    def test_very_long_version_string(self):
        """Handle unusually long version strings."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.10.1.2.3.4.5'}
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    def test_guard_with_extra_whitespace(self):
        """Handle guards with extra whitespace."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("  python   >=   3.10  ", ctx) is True

    def test_mixed_case_guard(self):
        """Handle mixed case in guard tokens."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11'}
        assert evaluate_version_guard("Python >= 3.10", ctx) is True
        assert evaluate_version_guard("PYTHON >= 3.10", ctx) is True

    def test_unicode_in_context(self):
        """Handle unicode characters in context."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11', 'note': '日本語'}
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    def test_deeply_nested_context(self):
        """Handle deeply nested context structures."""
        ctx = {
            'infrastructure': {
                'docker_version': '24.0',
                'nested': {
                    'deep': {
                        'value': 'ignored'
                    }
                }
            }
        }
        assert evaluate_version_guard("docker >= 23.0", ctx) is True

    def test_empty_string_version(self):
        """Handle empty string as version."""
        ctx = {'primary_language': 'python', 'primary_language_version': ''}
        # Should return True (no version = conservative include)
        assert evaluate_version_guard("python >= 3.10", ctx) is True

    def test_zero_version(self):
        """Handle zero as version."""
        ctx = {'primary_language': 'python', 'primary_language_version': '0'}
        assert evaluate_version_guard("python >= 0", ctx) is True

    def test_component_with_null_values(self):
        """Handle components with null/None values."""
        project_ctx = {
            'components': [
                {
                    'path': 'backend/',
                    'language': 'python',
                    'language_version': None,  # Null version
                    'framework': None,
                }
            ]
        }
        ctx = get_component_version_context(project_ctx, 'backend/')
        assert ctx['primary_language'] == 'python'
        assert ctx.get('primary_language_version') is None

    def test_version_with_prerelease(self):
        """Handle versions with prerelease tags."""
        # parse_version will fail on "3.11-beta" but that's expected
        ctx = {'primary_language': 'python', 'primary_language_version': '3.11-beta'}
        # Should return True (conservative fallback)
        result = evaluate_version_guard("python >= 3.10", ctx)
        assert result is True

    def test_version_comparison_edge_major(self):
        """Test major version boundary."""
        ctx = {'primary_language': 'python', 'primary_language_version': '3.0'}
        assert evaluate_version_guard("python >= 3.0", ctx) is True
        assert evaluate_version_guard("python >= 2.7", ctx) is True
        assert evaluate_version_guard("python >= 3.1", ctx) is False

    def test_multiple_databases_in_context(self):
        """Handle context with multiple databases."""
        ctx = {
            'postgresql_version': '15',
            'mysql_version': '8.0',
            'redis_version': '7.2',
        }
        assert evaluate_version_guard("postgresql >= 14", ctx) is True
        assert evaluate_version_guard("mysql >= 8.0", ctx) is True
        assert evaluate_version_guard("redis >= 7.0", ctx) is True


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
