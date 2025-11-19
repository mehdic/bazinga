#!/usr/bin/env python3
"""Pattern detection for architectural patterns."""

import os
from typing import Dict, Any


class PatternDetector:
    def detect_patterns(self) -> Dict[str, Any]:
        """Detect architectural patterns in the codebase."""
        patterns = {}

        # Check for service layer
        if self._directory_exists(["services", "service", "src/services"]):
            patterns["service_layer"] = True

        # Check for repository pattern
        if self._directory_exists(["repositories", "repository", "repo", "src/repositories"]):
            patterns["repository_pattern"] = True

        # Check for MVC
        mvc_dirs = ["models", "views", "controllers"]
        if all(self._directory_exists([d]) for d in mvc_dirs):
            patterns["mvc"] = True

        # Check for factory pattern
        if self._directory_exists(["factories", "factory"]) or self._file_pattern_exists("factory"):
            patterns["factory_pattern"] = True

        # Check for decorator pattern
        if self._file_pattern_exists("decorator") or self._file_pattern_exists("@"):
            patterns["decorator_pattern"] = True

        # Detect testing framework
        patterns["test_framework"] = self._detect_test_framework()

        # Detect build system
        patterns["build_system"] = self._detect_build_system()

        # Detect package manager
        patterns["package_manager"] = self._detect_package_manager()

        # Detect primary language
        patterns["primary_language"] = self._detect_primary_language()

        return patterns

    def _directory_exists(self, possible_paths: list) -> bool:
        """Check if any of the possible directory paths exist."""
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return True
        return False

    def _file_pattern_exists(self, pattern: str) -> bool:
        """Check if files matching pattern exist in the codebase."""
        for root, dirs, files in os.walk("."):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build', '__pycache__']]
            
            for file in files:
                if pattern.lower() in file.lower():
                    return True
        return False

    def _detect_test_framework(self) -> str:
        """Detect the testing framework being used."""
        # Check pytest.ini first (most specific)
        if os.path.exists("pytest.ini"):
            return "pytest"

        # Check setup.cfg for pytest config
        if os.path.exists("setup.cfg"):
            try:
                with open("setup.cfg", "r") as f:
                    content = f.read()
                    if "[tool:pytest]" in content or "pytest" in content:
                        return "pytest"
            except:
                pass

        # Check pyproject.toml for pytest config
        if os.path.exists("pyproject.toml"):
            try:
                with open("pyproject.toml", "r") as f:
                    content = f.read()
                    if "pytest" in content or "[tool.pytest" in content:
                        return "pytest"
            except:
                pass
        elif os.path.exists("jest.config.js") or os.path.exists("jest.config.ts"):
            return "jest"
        elif os.path.exists("karma.conf.js"):
            return "karma"
        elif os.path.exists("mocha.opts") or self._file_pattern_exists("mocha"):
            return "mocha"
        elif os.path.exists("go.mod"):
            return "go test"
        elif os.path.exists("pom.xml"):
            # Maven project, likely JUnit
            return "junit"
        elif os.path.exists("build.gradle") or os.path.exists("build.gradle.kts"):
            return "junit"
        elif os.path.exists("Cargo.toml"):
            return "cargo test"
        elif self._directory_exists(["test", "tests", "spec"]):
            # Generic test directory exists
            return "unknown (test directory found)"
        else:
            return "none detected"

    def _detect_build_system(self) -> str:
        """Detect the build system being used."""
        if os.path.exists("Makefile"):
            return "make"
        elif os.path.exists("package.json"):
            return "npm/yarn"
        elif os.path.exists("pom.xml"):
            return "maven"
        elif os.path.exists("build.gradle") or os.path.exists("build.gradle.kts"):
            return "gradle"
        elif os.path.exists("Cargo.toml"):
            return "cargo"
        elif os.path.exists("setup.py") or os.path.exists("pyproject.toml"):
            return "setuptools/pip"
        elif os.path.exists("go.mod"):
            return "go modules"
        elif os.path.exists("CMakeLists.txt"):
            return "cmake"
        elif os.path.exists("Rakefile"):
            return "rake"
        else:
            return "none detected"

    def _detect_package_manager(self) -> str:
        """Detect the package manager being used."""
        if os.path.exists("package-lock.json"):
            return "npm"
        elif os.path.exists("yarn.lock"):
            return "yarn"
        elif os.path.exists("pnpm-lock.yaml"):
            return "pnpm"
        elif os.path.exists("Pipfile.lock"):
            return "pipenv"
        elif os.path.exists("poetry.lock"):
            return "poetry"
        elif os.path.exists("requirements.txt"):
            return "pip"
        elif os.path.exists("go.sum"):
            return "go modules"
        elif os.path.exists("Cargo.lock"):
            return "cargo"
        elif os.path.exists("Gemfile.lock"):
            return "bundler"
        elif os.path.exists("composer.lock"):
            return "composer"
        else:
            return "none detected"

    def _detect_primary_language(self) -> str:
        """Detect the primary programming language."""
        file_counts = {
            'python': 0,
            'javascript': 0,
            'typescript': 0,
            'java': 0,
            'go': 0,
            'rust': 0,
            'ruby': 0,
            'php': 0,
            'csharp': 0,
            'cpp': 0
        }

        for root, dirs, files in os.walk("."):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build', '__pycache__', 'vendor']]
            
            for file in files:
                if file.endswith('.py'):
                    file_counts['python'] += 1
                elif file.endswith('.js'):
                    file_counts['javascript'] += 1
                elif file.endswith('.ts') or file.endswith('.tsx'):
                    file_counts['typescript'] += 1
                elif file.endswith('.java'):
                    file_counts['java'] += 1
                elif file.endswith('.go'):
                    file_counts['go'] += 1
                elif file.endswith('.rs'):
                    file_counts['rust'] += 1
                elif file.endswith('.rb'):
                    file_counts['ruby'] += 1
                elif file.endswith('.php'):
                    file_counts['php'] += 1
                elif file.endswith('.cs'):
                    file_counts['csharp'] += 1
                elif file.endswith('.cpp') or file.endswith('.cc') or file.endswith('.h'):
                    file_counts['cpp'] += 1

        # Return the language with the most files
        if max(file_counts.values()) > 0:
            return max(file_counts, key=file_counts.get)
        else:
            return "unknown"
