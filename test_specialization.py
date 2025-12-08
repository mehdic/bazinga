#!/usr/bin/env python3
"""
Comprehensive test of the specialization system.
Tests: mapping table, normalization, template existence, and full flow.
"""

import os
import re
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def ok(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"{RED}✗{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

# =============================================================================
# MAPPING TABLE (from project_manager.md Step 3.5.1b)
# =============================================================================

MAPPING_TABLE = {
    "typescript": "bazinga/templates/specializations/01-languages/typescript.md",
    "javascript": "bazinga/templates/specializations/01-languages/javascript.md",
    "python": "bazinga/templates/specializations/01-languages/python.md",
    "java": "bazinga/templates/specializations/01-languages/java.md",
    "go": "bazinga/templates/specializations/01-languages/go.md",
    "rust": "bazinga/templates/specializations/01-languages/rust.md",
    "react": "bazinga/templates/specializations/02-frameworks-frontend/react.md",
    "nextjs": "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md",
    "vue": "bazinga/templates/specializations/02-frameworks-frontend/vue.md",
    "angular": "bazinga/templates/specializations/02-frameworks-frontend/angular.md",
    "express": "bazinga/templates/specializations/03-frameworks-backend/express.md",
    "fastapi": "bazinga/templates/specializations/03-frameworks-backend/fastapi.md",
    "django": "bazinga/templates/specializations/03-frameworks-backend/django.md",
    "springboot": "bazinga/templates/specializations/03-frameworks-backend/spring-boot.md",
    "kubernetes": "bazinga/templates/specializations/06-infrastructure/kubernetes.md",
    "docker": "bazinga/templates/specializations/06-infrastructure/docker.md",
    "postgresql": "bazinga/templates/specializations/05-databases/postgresql.md",
    "mongodb": "bazinga/templates/specializations/05-databases/mongodb.md",
    "playwright": "bazinga/templates/specializations/08-testing/playwright-cypress.md",
    "cypress": "bazinga/templates/specializations/08-testing/playwright-cypress.md",
    "jest": "bazinga/templates/specializations/08-testing/jest-vitest.md",
    "vitest": "bazinga/templates/specializations/08-testing/jest-vitest.md",
}

ALIAS_MAP = {
    "k8s": "kubernetes",
    "ts": "typescript",
    "js": "javascript",
    "py": "python",
    "pg": "postgresql",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "next": "nextjs",
    "spring": "springboot",
    "golang": "go",
    "reactjs": "react",
    "vuejs": "vue",
    "expressjs": "express",
}

# =============================================================================
# HELPER FUNCTIONS (from project_manager.md)
# =============================================================================

def remove_punctuation(text):
    """Remove punctuation but keep + and # for C++/C#."""
    result = ""
    for char in text:
        if char.isalnum() or char.isspace() or char in ['+', '#']:
            result += char
    return result

def remove_whitespace(text):
    """Remove all whitespace."""
    return re.sub(r'\s', '', text)

def normalize_key(input_str):
    """Normalize input to canonical key."""
    key = input_str.lower().strip()
    key = remove_punctuation(key)
    key = remove_whitespace(key)

    if key in ALIAS_MAP:
        key = ALIAS_MAP[key]

    return key

def file_exists(path):
    """Check if file exists and is a file (not directory)."""
    return os.path.isfile(path)

def lookup_and_validate(input_str):
    """Lookup with normalization and file existence check."""
    key = normalize_key(input_str)
    path = MAPPING_TABLE.get(key)

    if path is None:
        return None, f"Technology '{input_str}' (normalized: '{key}') not in mapping table"

    if not file_exists(path):
        return None, f"Template file does not exist: {path}"

    return path, None

def parse_frameworks(framework_string):
    """Parse framework string like 'React (Frontend), Express (Backend)'."""
    parts = framework_string.split(",")
    frameworks = []
    for part in parts:
        clean = part
        if "(" in clean:
            start = clean.find("(")
            end = clean.find(")", start)
            if end > start:
                clean = clean[:start] + clean[end+1:]
        clean = clean.strip()
        if clean:
            frameworks.append(clean)
    return frameworks

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_normalization():
    """Test the normalization function."""
    print("\n" + "="*60)
    print("TEST 1: Normalization")
    print("="*60)

    test_cases = [
        # (input, expected_normalized)
        ("TypeScript", "typescript"),
        ("typescript", "typescript"),
        ("TYPESCRIPT", "typescript"),
        ("Next.js", "nextjs"),
        ("next.js", "nextjs"),
        ("Spring Boot", "springboot"),
        ("spring-boot", "springboot"),
        ("k8s", "kubernetes"),
        ("K8s", "kubernetes"),
        ("ts", "typescript"),
        ("JS", "javascript"),
        ("py", "python"),
        ("PostgreSQL", "postgresql"),
        ("postgres", "postgresql"),
        ("pg", "postgresql"),
        ("MongoDB", "mongodb"),
        ("mongo", "mongodb"),
        ("reactjs", "react"),
        ("React.js", "react"),  # "." removed → "reactjs" → alias to "react"
        ("vuejs", "vue"),
        ("expressjs", "express"),
        ("golang", "go"),
        ("Go", "go"),
        ("C++", "c++"),  # Should preserve ++
        ("C#", "c#"),    # Should preserve #
    ]

    passed = 0
    failed = 0

    for input_val, expected in test_cases:
        result = normalize_key(input_val)
        if result == expected:
            ok(f"'{input_val}' → '{result}'")
            passed += 1
        else:
            fail(f"'{input_val}' → '{result}' (expected '{expected}')")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_template_files_exist():
    """Test that all template files in MAPPING_TABLE exist."""
    print("\n" + "="*60)
    print("TEST 2: Template Files Exist")
    print("="*60)

    # Get unique paths
    unique_paths = set(MAPPING_TABLE.values())

    passed = 0
    failed = 0

    for path in sorted(unique_paths):
        if file_exists(path):
            ok(f"{path}")
            passed += 1
        else:
            fail(f"{path} - FILE NOT FOUND")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_lookup_and_validate():
    """Test the full lookup_and_validate function."""
    print("\n" + "="*60)
    print("TEST 3: Lookup and Validate")
    print("="*60)

    test_cases = [
        # Technologies that should work
        "TypeScript",
        "JavaScript",
        "Python",
        "React",
        "Next.js",
        "Vue",
        "Express",
        "FastAPI",
        "Django",
        "Spring Boot",
        "Kubernetes",
        "k8s",
        "Docker",
        "PostgreSQL",
        "postgres",
        "MongoDB",
        "Playwright",
        "Cypress",
        "Jest",
        "Vitest",
    ]

    passed = 0
    failed = 0

    for tech in test_cases:
        path, error = lookup_and_validate(tech)
        if path:
            ok(f"'{tech}' → {path}")
            passed += 1
        else:
            fail(f"'{tech}' → {error}")
            failed += 1

    # Test some that should fail
    print("\n--- Expected failures (unknown technologies) ---")
    unknown_techs = ["Ruby", "Perl", "Haskell", "Scala"]
    for tech in unknown_techs:
        path, error = lookup_and_validate(tech)
        if path is None:
            ok(f"'{tech}' correctly returned None")
        else:
            fail(f"'{tech}' unexpectedly returned {path}")

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_parse_frameworks():
    """Test the parse_frameworks function."""
    print("\n" + "="*60)
    print("TEST 4: Parse Frameworks")
    print("="*60)

    test_cases = [
        ("React", ["React"]),
        ("React (Frontend)", ["React"]),
        ("React (Frontend), Express (Backend)", ["React", "Express"]),
        ("TypeScript, React, Node.js", ["TypeScript", "React", "Node.js"]),
        ("Next.js (SSR), FastAPI (API)", ["Next.js", "FastAPI"]),
    ]

    passed = 0
    failed = 0

    for input_val, expected in test_cases:
        result = parse_frameworks(input_val)
        if result == expected:
            ok(f"'{input_val}' → {result}")
            passed += 1
        else:
            fail(f"'{input_val}' → {result} (expected {expected})")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_full_flow():
    """Test the full specialization flow with mock project_context."""
    print("\n" + "="*60)
    print("TEST 5: Full Flow (Mock project_context)")
    print("="*60)

    # Simulate project_context.json scenarios
    scenarios = [
        {
            "name": "TypeScript + Express project",
            "project_context": {
                "primary_language": "TypeScript",
                "framework": "Express (Backend)",
            },
            "expected_count": 2,  # typescript + express
        },
        {
            "name": "React + Next.js frontend",
            "project_context": {
                "primary_language": "TypeScript",
                "framework": "Next.js (Frontend)",
            },
            "expected_count": 2,  # typescript + nextjs
        },
        {
            "name": "Full stack with DB",
            "project_context": {
                "primary_language": "Python",
                "framework": "FastAPI (Backend)",
                "database": "PostgreSQL",
            },
            "expected_count": 3,  # python + fastapi + postgresql
        },
        {
            "name": "Multi-framework",
            "project_context": {
                "primary_language": "TypeScript",
                "framework": "React (Frontend), Express (Backend)",
                "database": "MongoDB",
                "testing": "Jest",
            },
            "expected_count": 5,  # typescript + react + express + mongodb + jest
        },
        {
            "name": "Infrastructure focused",
            "project_context": {
                "primary_language": "Go",
                "infrastructure": "Kubernetes, Docker",
            },
            "expected_count": 3,  # go + kubernetes + docker
        },
    ]

    passed = 0
    failed = 0

    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        pc = scenario["project_context"]
        specializations = []

        # Map primary_language
        if "primary_language" in pc:
            path, _ = lookup_and_validate(pc["primary_language"])
            if path:
                specializations.append(path)

        # Map framework(s)
        if "framework" in pc:
            frameworks = parse_frameworks(pc["framework"])
            for fw in frameworks:
                path, _ = lookup_and_validate(fw)
                if path:
                    specializations.append(path)

        # Map database
        if "database" in pc:
            dbs = parse_frameworks(pc["database"])
            for db in dbs:
                path, _ = lookup_and_validate(db)
                if path:
                    specializations.append(path)

        # Map infrastructure
        if "infrastructure" in pc:
            infras = parse_frameworks(pc["infrastructure"])
            for infra in infras:
                path, _ = lookup_and_validate(infra)
                if path:
                    specializations.append(path)

        # Map testing
        if "testing" in pc:
            tests = parse_frameworks(pc["testing"])
            for test in tests:
                path, _ = lookup_and_validate(test)
                if path:
                    specializations.append(path)

        # Dedupe
        seen = set()
        unique_specs = []
        for spec in specializations:
            if spec not in seen:
                seen.add(spec)
                unique_specs.append(spec)

        print(f"  Input: {pc}")
        print(f"  Output: {unique_specs}")

        if len(unique_specs) == scenario["expected_count"]:
            ok(f"Got {len(unique_specs)} specializations (expected {scenario['expected_count']})")
            passed += 1
        else:
            fail(f"Got {len(unique_specs)} specializations (expected {scenario['expected_count']})")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_template_content():
    """Test that template files have valid content."""
    print("\n" + "="*60)
    print("TEST 6: Template Content Validation")
    print("="*60)

    unique_paths = set(MAPPING_TABLE.values())

    passed = 0
    failed = 0
    warnings = 0

    for path in sorted(unique_paths):
        if not file_exists(path):
            continue

        with open(path, 'r') as f:
            content = f.read()

        issues = []

        # Check for required sections
        if "---" not in content[:500]:
            issues.append("Missing YAML frontmatter")

        if "## Patterns to Follow" not in content and "## Patterns" not in content:
            issues.append("Missing 'Patterns to Follow' section")

        if "## Patterns to Avoid" not in content:
            issues.append("Missing 'Patterns to Avoid' section")

        if len(content) < 500:
            issues.append(f"Content too short ({len(content)} chars)")

        if issues:
            warn(f"{path}: {', '.join(issues)}")
            warnings += 1
        else:
            ok(f"{path} (valid)")
            passed += 1

    print(f"\nResults: {passed} valid, {warnings} warnings")
    return True  # Warnings don't fail the test

def main():
    """Run all tests."""
    print("="*60)
    print("SPECIALIZATION SYSTEM - COMPREHENSIVE TEST")
    print("="*60)

    results = []

    results.append(("Normalization", test_normalization()))
    results.append(("Template Files Exist", test_template_files_exist()))
    results.append(("Lookup and Validate", test_lookup_and_validate()))
    results.append(("Parse Frameworks", test_parse_frameworks()))
    results.append(("Full Flow", test_full_flow()))
    results.append(("Template Content", test_template_content()))

    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(f"{GREEN}All tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}Some tests failed!{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())
