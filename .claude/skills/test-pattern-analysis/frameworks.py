#!/usr/bin/env python3
"""
Test Framework Detection

Detects which test framework is being used in the project.
"""

import os
import re
from typing import Optional


def detect_framework(test_path: str) -> str:
    """
    Detect which test framework is being used.

    Args:
        test_path: Path to test directory or file

    Returns:
        Framework name: "pytest", "jest", "go", "junit", "rspec", "unknown"
    """
    # Get the root directory (go up from test path if needed)
    if os.path.isfile(test_path):
        root_dir = os.path.dirname(test_path)
    else:
        root_dir = test_path

    # Go up to project root (look for common root indicators)
    while root_dir and root_dir != '/':
        if os.path.exists(os.path.join(root_dir, '.git')):
            break
        if os.path.exists(os.path.join(root_dir, 'package.json')):
            break
        if os.path.exists(os.path.join(root_dir, 'go.mod')):
            break
        if os.path.exists(os.path.join(root_dir, 'pom.xml')):
            break
        parent = os.path.dirname(root_dir)
        if parent == root_dir:
            break
        root_dir = parent

    # pytest indicators
    if (os.path.exists(os.path.join(root_dir, 'pytest.ini')) or
        os.path.exists(os.path.join(root_dir, 'setup.cfg')) or
        os.path.exists(os.path.join(test_path, 'conftest.py')) or
        has_pytest_in_file(test_path)):
        return "pytest"

    # jest indicators
    if (os.path.exists(os.path.join(root_dir, 'jest.config.js')) or
        os.path.exists(os.path.join(root_dir, 'jest.config.json')) or
        has_jest_in_package_json(root_dir) or
        has_jest_in_file(test_path)):
        return "jest"

    # go test indicators
    if (os.path.exists(os.path.join(root_dir, 'go.mod')) or
        has_go_test_files(test_path)):
        return "go"

    # JUnit indicators
    if (os.path.exists(os.path.join(root_dir, 'pom.xml')) or
        os.path.exists(os.path.join(root_dir, 'build.gradle')) or
        has_junit_in_file(test_path)):
        return "junit"

    # RSpec indicators
    if (os.path.exists(os.path.join(root_dir, '.rspec')) or
        has_rspec_in_file(test_path)):
        return "rspec"

    return "unknown"


def has_pytest_in_file(test_path: str) -> bool:
    """Check if file contains pytest markers."""
    if not os.path.exists(test_path):
        return False

    if os.path.isfile(test_path):
        files = [test_path]
    else:
        files = [os.path.join(test_path, f) for f in os.listdir(test_path)
                 if f.endswith('.py')][:5]  # Check first 5 files

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '@pytest.' in content or 'import pytest' in content:
                    return True
        except Exception:
            continue

    return False


def has_jest_in_package_json(root_dir: str) -> bool:
    """Check if package.json contains jest."""
    package_json = os.path.join(root_dir, 'package.json')
    if not os.path.exists(package_json):
        return False

    try:
        with open(package_json, 'r') as f:
            content = f.read()
            return 'jest' in content.lower()
    except Exception:
        return False


def has_jest_in_file(test_path: str) -> bool:
    """Check if file contains jest markers."""
    if not os.path.exists(test_path):
        return False

    if os.path.isfile(test_path):
        files = [test_path]
    else:
        files = [os.path.join(test_path, f) for f in os.listdir(test_path)
                 if f.endswith(('.test.js', '.test.ts', '.test.tsx'))][:5]

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'describe(' in content or 'test(' in content or 'expect(' in content:
                    return True
        except Exception:
            continue

    return False


def has_go_test_files(test_path: str) -> bool:
    """Check if directory contains Go test files."""
    if not os.path.exists(test_path):
        return False

    if os.path.isfile(test_path):
        return test_path.endswith('_test.go')
    else:
        for f in os.listdir(test_path):
            if f.endswith('_test.go'):
                return True

    return False


def has_junit_in_file(test_path: str) -> bool:
    """Check if file contains JUnit markers."""
    if not os.path.exists(test_path):
        return False

    if os.path.isfile(test_path):
        files = [test_path]
    else:
        files = [os.path.join(test_path, f) for f in os.listdir(test_path)
                 if f.endswith('.java')][:5]

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '@Test' in content or 'import org.junit' in content:
                    return True
        except Exception:
            continue

    return False


def has_rspec_in_file(test_path: str) -> bool:
    """Check if file contains RSpec markers."""
    if not os.path.exists(test_path):
        return False

    if os.path.isfile(test_path):
        files = [test_path]
    else:
        files = [os.path.join(test_path, f) for f in os.listdir(test_path)
                 if f.endswith('_spec.rb')][:5]

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'describe ' in content or 'it ' in content or 'expect(' in content:
                    return True
        except Exception:
            continue

    return False


def get_framework_version(framework: str) -> Optional[str]:
    """
    Get version of the test framework (if possible).

    Args:
        framework: Framework name

    Returns:
        Version string or None
    """
    if framework == "pytest":
        return get_pytest_version()
    elif framework == "jest":
        return get_jest_version()
    elif framework == "go":
        return get_go_version()
    elif framework == "junit":
        return get_junit_version()

    return None


def get_pytest_version() -> Optional[str]:
    """Get pytest version from requirements or installed packages."""
    # Check requirements.txt
    if os.path.exists('requirements.txt'):
        try:
            with open('requirements.txt', 'r') as f:
                for line in f:
                    if 'pytest' in line:
                        match = re.search(r'pytest[=><!~]+([0-9.]+)', line)
                        if match:
                            return match.group(1)
        except Exception:
            pass

    return None


def get_jest_version() -> Optional[str]:
    """Get jest version from package.json."""
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r') as f:
                content = f.read()
                # Look for "jest": "^29.0.0" pattern
                match = re.search(r'"jest"\s*:\s*"[\^~]?([0-9.]+)"', content)
                if match:
                    return match.group(1)
        except Exception:
            pass

    return None


def get_go_version() -> Optional[str]:
    """Get Go version from go.mod."""
    if os.path.exists('go.mod'):
        try:
            with open('go.mod', 'r') as f:
                for line in f:
                    if line.startswith('go '):
                        version = line.split()[1].strip()
                        return version
        except Exception:
            pass

    return None


def get_junit_version() -> Optional[str]:
    """Get JUnit version from pom.xml or build.gradle."""
    # Check pom.xml
    if os.path.exists('pom.xml'):
        try:
            with open('pom.xml', 'r') as f:
                content = f.read()
                match = re.search(r'<artifactId>junit</artifactId>\s*<version>([0-9.]+)</version>', content)
                if match:
                    return match.group(1)
        except Exception:
            pass

    # Check build.gradle
    if os.path.exists('build.gradle'):
        try:
            with open('build.gradle', 'r') as f:
                content = f.read()
                match = re.search(r'junit.*:([0-9.]+)', content)
                if match:
                    return match.group(1)
        except Exception:
            pass

    return None


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python frameworks.py <test_path>")
        sys.exit(1)

    test_path = sys.argv[1]
    framework = detect_framework(test_path)
    version = get_framework_version(framework)

    print(f"Framework: {framework}")
    if version:
        print(f"Version: {version}")
