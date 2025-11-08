#!/usr/bin/env python3
"""
Pattern Detection Functions

Detects architectural patterns, utilities, and conventions in the codebase.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any


def detect_patterns() -> List[str]:
    """
    Detect architectural patterns in the codebase.

    Returns:
        List of detected patterns
    """
    patterns = []

    # Service layer pattern
    if os.path.exists("services") or os.path.exists("src/services"):
        patterns.append("Service layer pattern (services/)")

    # Repository pattern
    if os.path.exists("repositories") or os.path.exists("repos") or os.path.exists("src/repositories"):
        patterns.append("Repository pattern (repositories/)")

    # Factory pattern
    factory_files = []
    for root, dirs, files in os.walk("."):
        if "node_modules" in root or ".git" in root or "venv" in root:
            continue
        for file in files:
            if "factory" in file.lower():
                factory_files.append(file)

    if factory_files:
        patterns.append("Factory pattern (factory files)")

    # MVC pattern
    has_models = os.path.exists("models") or os.path.exists("src/models")
    has_views = os.path.exists("views") or os.path.exists("src/views") or os.path.exists("templates")
    has_controllers = os.path.exists("controllers") or os.path.exists("src/controllers")

    if has_models and has_views and has_controllers:
        patterns.append("MVC pattern (models/views/controllers)")
    elif has_models and has_controllers:
        patterns.append("Model-Controller pattern")

    # Middleware pattern
    if os.path.exists("middleware") or os.path.exists("src/middleware"):
        patterns.append("Middleware pattern (middleware/)")

    # Dependency injection
    # Check for common DI files/patterns
    di_indicators = ["container.py", "dependencies.py", "inject.py", "di.py"]
    for indicator in di_indicators:
        if os.path.exists(indicator) or os.path.exists(f"src/{indicator}"):
            patterns.append("Dependency injection pattern")
            break

    # API structure patterns
    if os.path.exists("api") or os.path.exists("src/api"):
        patterns.append("API layer pattern (api/)")

    # Clean architecture layers
    has_domain = os.path.exists("domain") or os.path.exists("src/domain")
    has_application = os.path.exists("application") or os.path.exists("src/application")
    has_infrastructure = os.path.exists("infrastructure") or os.path.exists("src/infrastructure")

    if has_domain and has_application and has_infrastructure:
        patterns.append("Clean architecture (domain/application/infrastructure)")

    return patterns


def find_utilities() -> List[Dict[str, Any]]:
    """
    Find reusable utility modules in the codebase.

    Returns:
        List of utility modules with their functions
    """
    utilities = []

    # Common utility directories
    utility_dirs = [
        "utils", "lib", "helpers", "common", "shared",
        "src/utils", "src/lib", "src/helpers", "src/common", "src/shared"
    ]

    for util_dir in utility_dirs:
        if not os.path.exists(util_dir):
            continue

        # Find all files in utility directory
        for root, dirs, files in os.walk(util_dir):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            for file in files:
                # Skip non-code files
                if not file.endswith(('.py', '.js', '.ts', '.go', '.java', '.rb')):
                    continue

                filepath = os.path.join(root, file)

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Extract functions/classes
                    functions = extract_utility_functions(content, filepath)

                    if functions:
                        # Determine utility name (class or module name)
                        utility_name = determine_utility_name(content, file)

                        utilities.append({
                            "name": utility_name,
                            "file": filepath,
                            "functions": functions[:10]  # Limit to top 10
                        })
                except Exception:
                    continue

    return utilities


def extract_utility_functions(content: str, filepath: str) -> List[str]:
    """
    Extract function names from utility file.

    Args:
        content: File content
        filepath: File path

    Returns:
        List of function names
    """
    functions = []

    # Python
    if filepath.endswith('.py'):
        # Public functions (not starting with _)
        functions.extend(re.findall(r'def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\(', content))

    # JavaScript/TypeScript
    elif filepath.endswith(('.js', '.ts', '.tsx', '.jsx')):
        # Functions
        functions.extend(re.findall(r'function\s+(\w+)\s*\(', content))
        # Arrow functions
        functions.extend(re.findall(r'(?:export\s+)?const\s+(\w+)\s*=\s*\(', content))
        # Methods in object/class
        functions.extend(re.findall(r'(\w+)\s*:\s*function\s*\(', content))

    # Go
    elif filepath.endswith('.go'):
        # Exported functions (start with uppercase)
        functions.extend(re.findall(r'func\s+([A-Z]\w*)\s*\(', content))

    # Java
    elif filepath.endswith('.java'):
        # Public methods
        functions.extend(re.findall(r'public\s+\w+\s+(\w+)\s*\(', content))

    # Ruby
    elif filepath.endswith('.rb'):
        # Public methods
        functions.extend(re.findall(r'def\s+(\w+)', content))

    return list(set(functions))  # Remove duplicates


def determine_utility_name(content: str, filename: str) -> str:
    """
    Determine the main utility name (class or module name).

    Args:
        content: File content
        filename: File name

    Returns:
        Utility name
    """
    # Try to find main class
    class_match = re.search(r'class\s+(\w+)', content)
    if class_match:
        return class_match.group(1)

    # Otherwise use filename (without extension)
    name = Path(filename).stem

    # Convert snake_case to PascalCase
    if '_' in name:
        name = ''.join(word.capitalize() for word in name.split('_'))
    else:
        name = name.capitalize()

    return name


def extract_conventions() -> List[str]:
    """
    Extract project conventions from configuration files and code analysis.

    Returns:
        List of conventions
    """
    conventions = []

    # Test coverage requirements
    if os.path.exists("pytest.ini"):
        try:
            with open("pytest.ini", 'r') as f:
                content = f.read()
                coverage_match = re.search(r'--cov-fail-under[=\s]+(\d+)', content)
                if coverage_match:
                    coverage_req = coverage_match.group(1)
                    conventions.append(f"Test coverage minimum: {coverage_req}%")
        except Exception:
            pass

    elif os.path.exists("jest.config.js") or os.path.exists("jest.config.json"):
        conventions.append("Test coverage tracked with Jest")

    # Linting configuration
    if os.path.exists(".eslintrc.json") or os.path.exists(".eslintrc.js"):
        conventions.append("ESLint for code style enforcement")

    if os.path.exists(".pylintrc") or os.path.exists("setup.cfg"):
        conventions.append("Pylint/flake8 for Python code style")

    # Code formatting
    if os.path.exists(".prettierrc") or os.path.exists(".prettierrc.json"):
        conventions.append("Prettier for code formatting")

    if os.path.exists("pyproject.toml"):
        try:
            with open("pyproject.toml", 'r') as f:
                if "black" in f.read():
                    conventions.append("Black for Python code formatting")
        except Exception:
            pass

    # Type checking
    if os.path.exists("tsconfig.json"):
        conventions.append("TypeScript for type safety")

    if os.path.exists("mypy.ini") or os.path.exists(".mypy.ini"):
        conventions.append("mypy for Python type checking")

    # Git hooks
    if os.path.exists(".pre-commit-config.yaml"):
        conventions.append("Pre-commit hooks for quality checks")

    # Documentation
    if os.path.exists("docs") and os.path.exists("mkdocs.yml"):
        conventions.append("MkDocs for project documentation")

    if os.path.exists("README.md"):
        conventions.append("README.md for project overview")

    # Error handling patterns
    error_response_files = []
    for root, dirs, files in os.walk("."):
        if any(x in root for x in [".git", "node_modules", "venv", "__pycache__"]):
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.ts')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "error_response" in content or "errorResponse" in content:
                            error_response_files.append(file)
                            if len(error_response_files) >= 3:
                                conventions.append("Use error_response() for standardized error handling")
                                break
                except Exception:
                    continue
        if len(error_response_files) >= 3:
            break

    # If no conventions found, add defaults
    if not conventions:
        conventions.append("Follow existing code patterns and style")

    return conventions


# Example usage
if __name__ == "__main__":
    print("Detecting patterns...")
    patterns = detect_patterns()
    print(f"Found {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"  - {pattern}")

    print("\nFinding utilities...")
    utilities = find_utilities()
    print(f"Found {len(utilities)} utilities:")
    for util in utilities[:5]:  # Show first 5
        print(f"  - {util['name']} ({util['file']})")
        print(f"    Functions: {', '.join(util['functions'][:5])}")

    print("\nExtracting conventions...")
    conventions = extract_conventions()
    print(f"Found {len(conventions)} conventions:")
    for convention in conventions:
        print(f"  - {convention}")
