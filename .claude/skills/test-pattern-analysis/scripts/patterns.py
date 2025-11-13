#!/usr/bin/env python3
"""
Test Pattern Extraction

Extracts fixtures, patterns, naming conventions, and utilities from test files.
"""

import os
import re
from typing import List, Dict, Any, Optional
from collections import Counter


def extract_fixtures(test_path: str, framework: str) -> List[Dict[str, Any]]:
    """
    Extract test fixtures based on framework.

    Args:
        test_path: Test directory path
        framework: Test framework name

    Returns:
        List of fixture definitions
    """
    if framework == "pytest":
        return extract_pytest_fixtures(test_path)
    elif framework == "jest":
        return extract_jest_fixtures(test_path)
    elif framework == "go":
        return extract_go_fixtures(test_path)
    elif framework == "junit":
        return extract_junit_fixtures(test_path)

    return []


def extract_pytest_fixtures(test_path: str) -> List[Dict[str, Any]]:
    """Extract pytest fixtures from conftest.py."""
    fixtures = []

    # Look for conftest.py
    conftest_paths = []
    if os.path.isfile(test_path) and test_path.endswith('conftest.py'):
        conftest_paths.append(test_path)
    elif os.path.isdir(test_path):
        for root, dirs, files in os.walk(test_path):
            if 'conftest.py' in files:
                conftest_paths.append(os.path.join(root, 'conftest.py'))

    for conftest_path in conftest_paths:
        try:
            with open(conftest_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find @pytest.fixture decorators
            pattern = r'@pytest\.fixture(?:\(([^)]*)\))?\s*\ndef\s+(\w+)'
            matches = re.finditer(pattern, content)

            for match in matches:
                params = match.group(1) or ""
                fixture_name = match.group(2)

                # Extract scope if present
                scope_match = re.search(r'scope=["\'](\w+)["\']', params)
                scope = scope_match.group(1) if scope_match else "function"

                # Try to extract docstring
                fixture_start = match.end()
                docstring_match = re.search(r'"""([^"]+)"""', content[fixture_start:fixture_start + 200])
                usage = docstring_match.group(1).strip() if docstring_match else f"Fixture: {fixture_name}"

                fixtures.append({
                    "name": fixture_name,
                    "file": conftest_path,
                    "scope": scope,
                    "usage": usage
                })
        except Exception:
            continue

    return fixtures


def extract_jest_fixtures(test_path: str) -> List[Dict[str, Any]]:
    """Extract jest setup functions (beforeEach, beforeAll, etc.)."""
    fixtures = []

    # Find test files
    test_files = []
    if os.path.isfile(test_path):
        test_files = [test_path]
    elif os.path.isdir(test_path):
        for root, dirs, files in os.walk(test_path):
            for file in files:
                if file.endswith(('.test.js', '.test.ts', '.test.tsx')):
                    test_files.append(os.path.join(root, file))
                    if len(test_files) >= 10:  # Limit for performance
                        break

    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find beforeEach, beforeAll
            for setup_type in ['beforeEach', 'beforeAll', 'afterEach', 'afterAll']:
                if setup_type in content:
                    scope = "function" if "Each" in setup_type else "module"
                    fixtures.append({
                        "name": setup_type,
                        "file": test_file,
                        "scope": scope,
                        "usage": f"Jest {setup_type} setup"
                    })
        except Exception:
            continue

    return fixtures[:10]  # Limit results


def extract_go_fixtures(test_path: str) -> List[Dict[str, Any]]:
    """Extract Go test setup functions."""
    fixtures = []

    # Find test files
    test_files = []
    if os.path.isfile(test_path):
        test_files = [test_path]
    elif os.path.isdir(test_path):
        for root, dirs, files in os.walk(test_path):
            for file in files:
                if file.endswith('_test.go'):
                    test_files.append(os.path.join(root, file))

    for test_file in test_files[:10]:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find setup/teardown functions
            setup_pattern = r'func\s+(setup\w*|teardown\w*)\s*\('
            matches = re.finditer(setup_pattern, content, re.IGNORECASE)

            for match in matches:
                func_name = match.group(1)
                fixtures.append({
                    "name": func_name,
                    "file": test_file,
                    "scope": "function",
                    "usage": f"Go test {func_name}"
                })
        except Exception:
            continue

    return fixtures


def extract_junit_fixtures(test_path: str) -> List[Dict[str, Any]]:
    """Extract JUnit @Before, @BeforeEach, etc."""
    fixtures = []

    # Find test files
    test_files = []
    if os.path.isfile(test_path):
        test_files = [test_path]
    elif os.path.isdir(test_path):
        for root, dirs, files in os.walk(test_path):
            for file in files:
                if file.endswith('Test.java'):
                    test_files.append(os.path.join(root, file))

    for test_file in test_files[:10]:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find @Before, @BeforeEach, @BeforeAll, etc.
            for annotation in ['@Before', '@BeforeEach', '@BeforeAll', '@After', '@AfterEach', '@AfterAll']:
                pattern = f'{annotation}\\s+public\\s+\\w+\\s+(\\w+)'
                matches = re.finditer(pattern, content)

                for match in matches:
                    method_name = match.group(1)
                    scope = "function" if "Each" in annotation or annotation == "@Before" else "class"
                    fixtures.append({
                        "name": method_name,
                        "file": test_file,
                        "scope": scope,
                        "usage": f"JUnit {annotation} setup"
                    })
        except Exception:
            continue

    return fixtures[:10]


def detect_test_structure(test_files: List[str], framework: str) -> Dict[str, str]:
    """
    Detect test structure pattern (AAA, Given-When-Then, etc.).

    Args:
        test_files: List of test files
        framework: Test framework

    Returns:
        Dictionary with structure and naming info
    """
    structure_votes = Counter()

    for test_file in test_files[:10]:  # Sample first 10 files
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for AAA pattern (Arrange-Act-Assert)
            if re.search(r'#\s*Arrange|#\s*Act|#\s*Assert', content, re.IGNORECASE):
                structure_votes['AAA (Arrange-Act-Assert)'] += 1
            elif re.search(r'//\s*Arrange|//\s*Act|//\s*Assert', content, re.IGNORECASE):
                structure_votes['AAA (Arrange-Act-Assert)'] += 1

            # Check for Given-When-Then (BDD)
            if re.search(r'#\s*Given|#\s*When|#\s*Then', content, re.IGNORECASE):
                structure_votes['BDD (Given-When-Then)'] += 1
            elif re.search(r'//\s*Given|//\s*When|//\s*Then', content, re.IGNORECASE):
                structure_votes['BDD (Given-When-Then)'] += 1

            # If no explicit comments, infer from structure
            # Look for setup, execution, assertion sections
            lines = content.split('\n')
            has_setup = any('setup' in line.lower() or 'create' in line.lower() for line in lines[:20])
            has_assert = any('assert' in line.lower() or 'expect' in line.lower() for line in lines)

            if has_setup and has_assert:
                structure_votes['AAA (Arrange-Act-Assert)'] += 0.5

        except Exception:
            continue

    # Get most common structure
    if structure_votes:
        structure = structure_votes.most_common(1)[0][0]
    else:
        structure = "AAA (Arrange-Act-Assert)"  # Default

    # Get example test name
    example = extract_example_test_name(test_files, framework)

    return {
        "structure": structure,
        "naming": extract_naming_pattern(test_files, framework),
        "example": example
    }


def extract_naming_pattern(test_files: List[str], framework: str) -> str:
    """
    Extract test naming convention.

    Args:
        test_files: List of test files
        framework: Test framework

    Returns:
        Naming pattern string
    """
    test_names = []

    for test_file in test_files[:10]:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if framework == "pytest":
                # Match: def test_xxx
                test_names.extend(re.findall(r'def\s+(test_\w+)', content))

            elif framework == "jest":
                # Match: test('xxx') or it('xxx')
                test_names.extend(re.findall(r'(?:test|it)\s*\(["\']([^"\']+)["\']', content))

            elif framework == "go":
                # Match: func TestXxx
                test_names.extend(re.findall(r'func\s+(Test\w+)', content))

            elif framework == "junit":
                # Match: @Test public void testXxx
                test_names.extend(re.findall(r'@Test\s+public\s+void\s+(test\w+)', content))

        except Exception:
            continue

    if not test_names:
        return "test_<feature>_<scenario>"

    # Analyze patterns
    if framework in ["pytest", "junit"]:
        # Check for underscore patterns
        underscore_count = sum(1 for name in test_names if '_' in name)
        if underscore_count > len(test_names) * 0.7:
            return "test_<function>_<scenario>_<expected>"
        else:
            return "test<Feature><Scenario>"

    elif framework == "jest":
        return "describe('feature') { test('scenario') }"

    elif framework == "go":
        return "Test<Feature><Scenario>"

    return "test_<feature>"


def extract_example_test_name(test_files: List[str], framework: str) -> str:
    """Extract an example test name."""
    for test_file in test_files[:5]:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if framework == "pytest":
                match = re.search(r'def\s+(test_\w+)', content)
                if match:
                    return match.group(1)

            elif framework == "jest":
                match = re.search(r'test\s*\(["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)

            elif framework == "go":
                match = re.search(r'func\s+(Test\w+)', content)
                if match:
                    return match.group(1)

            elif framework == "junit":
                match = re.search(r'@Test\s+public\s+void\s+(test\w+)', content)
                if match:
                    return match.group(1)

        except Exception:
            continue

    return "test_feature_scenario_expected"


def find_test_utilities(test_path: str) -> List[Dict[str, str]]:
    """
    Find test helper utilities.

    Args:
        test_path: Test directory

    Returns:
        List of utility functions
    """
    utilities = []

    # Common utility file names
    utility_files = ['helpers.py', 'fixtures.py', 'utils.py', 'test_helpers.js', 'test_utils.ts']

    if os.path.isdir(test_path):
        for root, dirs, files in os.walk(test_path):
            for file in files:
                if file in utility_files or 'helper' in file.lower() or 'util' in file.lower():
                    filepath = os.path.join(root, file)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Extract function names
                        if file.endswith('.py'):
                            func_names = re.findall(r'def\s+(\w+)\s*\(', content)
                        elif file.endswith(('.js', '.ts')):
                            func_names = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=)', content)
                            func_names = [n for n in func_names if n]
                        else:
                            continue

                        for func_name in func_names[:10]:
                            if isinstance(func_name, tuple):
                                func_name = next((n for n in func_name if n), None)
                            if func_name and not func_name.startswith('_'):
                                utilities.append({
                                    "name": func_name,
                                    "file": filepath
                                })

                    except Exception:
                        continue

    return utilities[:20]  # Limit results


def analyze_test_file(test_file: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a single test file.

    Args:
        test_file: Path to test file

    Returns:
        Analysis dictionary or None
    """
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count tests
        test_count = len(re.findall(r'def test_|test\(|func Test|@Test', content))

        # Extract edge cases from test names
        edge_cases = []
        test_names = re.findall(r'(?:def\s+test_|test\()["\']?(\w+)', content)
        for name in test_names:
            if any(keyword in name.lower() for keyword in ['invalid', 'error', 'fail', 'edge', 'empty', 'null']):
                edge_cases.append(name)

        return {
            "file": test_file,
            "test_count": test_count,
            "edge_cases": edge_cases[:5]  # Limit to 5
        }

    except Exception:
        return None


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python patterns.py <test_path> <framework>")
        sys.exit(1)

    test_path = sys.argv[1]
    framework = sys.argv[2]

    print(f"Extracting patterns for {framework}...")

    fixtures = extract_fixtures(test_path, framework)
    print(f"\nFixtures: {len(fixtures)}")
    for fixture in fixtures[:5]:
        print(f"  - {fixture['name']} ({fixture['scope']})")

    utilities = find_test_utilities(test_path)
    print(f"\nUtilities: {len(utilities)}")
    for util in utilities[:5]:
        print(f"  - {util['name']} in {util['file']}")
