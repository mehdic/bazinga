#!/usr/bin/env python3
"""
Test Pattern Analysis Skill - Main Script

Analyzes test suite to find patterns, fixtures, naming conventions, and utilities.

Usage:
    python analyze_tests.py tests/
    python analyze_tests.py tests/test_auth.py

Output:
    bazinga/artifacts/{SESSION_ID}/skills/test_patterns.json
"""

import os
import sys
import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add _shared directory to path for bazinga_paths import
# Assumes structure: .claude/skills/<skill_name>/scripts/<script>.py
# _shared is at: .claude/skills/_shared/
_script_dir = Path(__file__).parent.resolve()
_shared_dir = _script_dir.parent.parent / '_shared'
if _shared_dir.exists() and str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

try:
    from bazinga_paths import get_db_path, get_artifacts_dir
    _HAS_BAZINGA_PATHS = True
except ImportError:
    _HAS_BAZINGA_PATHS = False

def _get_db_path_safe() -> str:
    """Get database path with fallback for backward compatibility."""
    if _HAS_BAZINGA_PATHS:
        try:
            return str(get_db_path())
        except RuntimeError:
            pass
    return "bazinga/bazinga.db"

# Get current session ID from database
def get_current_session_id():
    """Get the most recent session ID from the database."""
    db_path = _get_db_path_safe()
    if not os.path.exists(db_path):
        return "bazinga_default"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return "bazinga_default"
    except:
        return "bazinga_default"

SESSION_ID = get_current_session_id()

# Use bazinga_paths for output directory if available
if _HAS_BAZINGA_PATHS:
    try:
        OUTPUT_DIR = get_artifacts_dir(session_id=SESSION_ID) / "skills"
    except RuntimeError:
        OUTPUT_DIR = Path(f"bazinga/artifacts/{SESSION_ID}/skills")
else:
    OUTPUT_DIR = Path(f"bazinga/artifacts/{SESSION_ID}/skills")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "test_patterns.json"

print(f"📁 Output directory: {OUTPUT_DIR}")

# Load profile for graceful degradation
def load_profile():
    """Load profile from skills_config.json"""
    try:
        with open("bazinga/skills_config.json", "r") as f:
            config = json.load(f)
            return config.get("_metadata", {}).get("profile", "lite")
    except:
        return "lite"

PROFILE = load_profile()

try:
    from frameworks import detect_framework, get_framework_version
    from patterns import (
        extract_fixtures,
        detect_test_structure,
        extract_naming_pattern,
        find_test_utilities,
        analyze_test_file
    )
except ImportError as e:
    # Graceful degradation if modules can't be imported
    if PROFILE == "lite":
        # Lite mode: Skip gracefully
        print(f"⚠️  Module import failed - test pattern analysis skipped in lite mode")
        print(f"   Error: {e}")
        output = {
            "status": "skipped",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "impact": "Test pattern analysis was skipped. Tests can still be written manually.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)
        sys.exit(0)
    else:
        # Advanced mode: Fail
        print(f"❌ Required modules not found: {e}")
        output = {
            "status": "error",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)
        sys.exit(1)


def find_test_files(path: str) -> List[str]:
    """
    Find all test files in the given path.

    Args:
        path: Directory or file path

    Returns:
        List of test file paths
    """
    test_files = []

    # If path is a file, return it
    if os.path.isfile(path):
        return [path]

    # If path is a directory, search for test files
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            for file in files:
                # Match test file patterns
                if (file.startswith('test_') or file.endswith('_test.py') or
                    file.endswith('.test.js') or file.endswith('.test.ts') or
                    file.endswith('_test.go') or file.endswith('Test.java')):
                    test_files.append(os.path.join(root, file))

    return test_files


def find_similar_tests(task_description: str, test_files: List[str]) -> List[Dict[str, Any]]:
    """
    Find tests similar to the current task.

    Args:
        task_description: Task description (if provided)
        test_files: List of test files

    Returns:
        List of similar test files with analysis
    """
    similar_tests = []

    for test_file in test_files[:10]:  # Limit to first 10 for performance
        try:
            analysis = analyze_test_file(test_file)
            if analysis:
                similar_tests.append(analysis)
        except Exception:
            continue

    return similar_tests


def suggest_test_cases(task_description: str, similar_tests: List[Dict], framework: str) -> List[str]:
    """
    Suggest test cases based on task and similar tests.

    Args:
        task_description: Task description
        similar_tests: Similar tests found
        framework: Test framework

    Returns:
        List of suggested test case names
    """
    suggestions = []

    # Extract feature name from task
    task_lower = task_description.lower() if task_description else ""

    # Extract main feature word
    feature_words = []
    for word in ["login", "register", "reset", "password", "email", "user", "auth", "token", "payment", "order"]:
        if word in task_lower:
            feature_words.append(word)

    feature = "_".join(feature_words) if feature_words else "feature"

    # Generate test suggestions based on framework
    if framework == "pytest":
        suggestions = [
            f"test_{feature}_valid_input_succeeds",
            f"test_{feature}_invalid_input_returns_error",
            f"test_{feature}_missing_required_field_raises_exception",
            f"test_{feature}_edge_case_handles_gracefully"
        ]
    elif framework == "jest":
        suggestions = [
            f"test('{feature} with valid input succeeds')",
            f"test('{feature} with invalid input returns error')",
            f"test('{feature} with missing field throws error')",
            f"test('{feature} edge case is handled')"
        ]
    elif framework == "go":
        feature_pascal = "".join(w.capitalize() for w in feature.split("_"))
        suggestions = [
            f"Test{feature_pascal}ValidInput",
            f"Test{feature_pascal}InvalidInput",
            f"Test{feature_pascal}MissingField",
            f"Test{feature_pascal}EdgeCase"
        ]
    elif framework == "junit":
        feature_camel = "".join(w.capitalize() if i > 0 else w for i, w in enumerate(feature.split("_")))
        suggestions = [
            f"test{feature_camel.capitalize()}WithValidInput",
            f"test{feature_camel.capitalize()}WithInvalidInput",
            f"test{feature_camel.capitalize()}WithMissingField",
            f"test{feature_camel.capitalize()}EdgeCase"
        ]

    return suggestions


def extract_coverage_target(test_dir: str, framework: str) -> Optional[str]:
    """
    Extract coverage target from configuration files.

    Args:
        test_dir: Test directory
        framework: Test framework

    Returns:
        Coverage target string (e.g., "80%") or None
    """
    # pytest
    if framework == "pytest":
        pytest_ini = "pytest.ini"
        if os.path.exists(pytest_ini):
            try:
                with open(pytest_ini, 'r') as f:
                    content = f.read()
                    match = re.search(r'--cov-fail-under[=\s]+(\d+)', content)
                    if match:
                        return f"{match.group(1)}%"
            except Exception:
                pass

    # jest
    elif framework == "jest":
        jest_configs = ["jest.config.js", "jest.config.json", "package.json"]
        for config_file in jest_configs:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        # Look for coverageThreshold
                        match = re.search(r'coverageThreshold["\']?\s*:\s*\{[^}]*global[^}]*branches["\']?\s*:\s*(\d+)', content)
                        if match:
                            return f"{match.group(1)}%"
                except Exception:
                    pass

    # Default
    return "80%"


def analyze_test_suite(test_path: str, task_description: str = "") -> Dict[str, Any]:
    """
    Main test suite analysis function.

    Args:
        test_path: Path to test directory or file
        task_description: Optional task description

    Returns:
        Analysis results as dictionary
    """
    print(f"🧪 Analyzing test suite at: {test_path}")

    # Step 1: Detect framework
    print("🔍 Detecting test framework...")
    framework = detect_framework(test_path)
    version = get_framework_version(framework)
    print(f"   Framework: {framework} {version if version else ''}")

    # Step 2: Find test files
    print("📁 Finding test files...")
    test_files = find_test_files(test_path)
    print(f"   Found {len(test_files)} test files")

    # Step 3: Extract fixtures
    print("🔧 Extracting fixtures...")
    fixtures = extract_fixtures(test_path, framework)
    print(f"   Found {len(fixtures)} fixtures")

    # Step 4: Detect test structure
    print("📐 Detecting test patterns...")
    test_patterns = detect_test_structure(test_files, framework)
    print(f"   Pattern: {test_patterns.get('structure', 'Unknown')}")

    # Step 5: Extract naming convention
    print("📝 Analyzing naming conventions...")
    naming_pattern = extract_naming_pattern(test_files, framework)
    print(f"   Naming: {naming_pattern}")

    # Step 6: Find test utilities
    print("🛠️  Finding test utilities...")
    utilities = find_test_utilities(test_path)
    print(f"   Found {len(utilities)} utilities")

    # Step 7: Find similar tests
    print("🔎 Finding similar tests...")
    similar_tests = find_similar_tests(task_description, test_files)
    print(f"   Found {len(similar_tests)} similar tests")

    # Step 8: Suggest test cases
    print("💡 Generating test suggestions...")
    suggested_tests = suggest_test_cases(task_description, similar_tests, framework)
    print(f"   Generated {len(suggested_tests)} suggestions")

    # Step 9: Extract coverage target
    print("📊 Extracting coverage target...")
    coverage_target = extract_coverage_target(test_path, framework)
    print(f"   Coverage target: {coverage_target}")

    # Build result
    result = {
        "framework": framework,
        "version": version,
        "test_directory": test_path,
        "common_fixtures": fixtures,
        "test_patterns": test_patterns,
        "similar_tests": similar_tests,
        "suggested_tests": suggested_tests,
        "coverage_target": coverage_target,
        "utilities": utilities
    }

    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_tests.py <test_directory> [task_description]")
        sys.exit(1)

    test_path = sys.argv[1]
    task_description = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.exists(test_path):
        print(f"Error: Path not found: {test_path}")
        sys.exit(1)

    # Run analysis
    result = analyze_test_suite(test_path, task_description)

    # Write output to session artifacts directory
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Analysis complete! Results written to: {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"   - Framework: {result['framework']}")
    print(f"   - Fixtures: {len(result['common_fixtures'])}")
    print(f"   - Pattern: {result['test_patterns'].get('structure', 'Unknown')}")
    print(f"   - Similar tests: {len(result['similar_tests'])}")
    print(f"   - Suggested tests: {len(result['suggested_tests'])}")
    print(f"   - Coverage target: {result['coverage_target']}")


if __name__ == "__main__":
    main()
