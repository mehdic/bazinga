#!/usr/bin/env python3
"""
Codebase analysis for providing context to developers.
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import supporting modules
from pattern_detector import PatternDetector
from similarity import SimilarityFinder
from cache_manager import CacheManager


class CodebaseAnalyzer:
    def __init__(self, task: str, session_id: str, cache_enabled: bool = True):
        self.task = task
        self.session_id = session_id
        self.cache_enabled = cache_enabled
        self.cache = CacheManager("bazinga/.analysis_cache") if cache_enabled else None
        self.pattern_detector = PatternDetector()
        self.similarity_finder = SimilarityFinder()

    def analyze(self) -> Dict[str, Any]:
        """Main analysis entry point."""
        results = {
            "task": self.task,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "cache_hits": 0,
            "cache_misses": 0
        }

        # Get or compute project patterns (cacheable)
        patterns_cache_key = "project_patterns"
        if self.cache and self.cache.get(patterns_cache_key, max_age_hours=1):
            results["project_patterns"] = self.cache.get(patterns_cache_key)
            results["cache_hits"] += 1
        else:
            results["project_patterns"] = self.pattern_detector.detect_patterns()
            if self.cache:
                self.cache.set(patterns_cache_key, results["project_patterns"])
            results["cache_misses"] += 1

        # Get or compute utilities (cacheable)
        utilities_cache_key = f"utilities_{self.session_id}"
        if self.cache and self.cache.get(utilities_cache_key):
            results["utilities"] = self.cache.get(utilities_cache_key)
            results["cache_hits"] += 1
        else:
            results["utilities"] = self.find_utilities()
            if self.cache:
                self.cache.set(utilities_cache_key, results["utilities"])
            results["cache_misses"] += 1

        # Find similar features (NOT cacheable - task specific)
        results["similar_features"] = self.similarity_finder.find_similar(self.task)
        results["cache_misses"] += 1

        # Generate suggestions based on analysis
        results["suggested_approach"] = self.generate_suggestions(results)

        # Calculate cache efficiency
        total_operations = results["cache_hits"] + results["cache_misses"]
        results["cache_efficiency"] = f"{(results['cache_hits'] / total_operations * 100):.1f}%" if total_operations > 0 else "0%"

        return results

    def find_utilities(self) -> List[Dict[str, Any]]:
        """Find reusable utilities in common directories."""
        utilities = []
        utility_dirs = ["utils", "helpers", "lib", "common", "shared", "utilities"]

        for dir_name in utility_dirs:
            # Check if directory exists at root level
            if os.path.exists(dir_name):
                utilities.extend(self.scan_utility_directory(dir_name))
            
            # Check in src/ or lib/ subdirectories
            for parent in ["src", "lib", "app"]:
                path = os.path.join(parent, dir_name)
                if os.path.exists(path):
                    utilities.extend(self.scan_utility_directory(path))

        return utilities

    def scan_utility_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """Scan a utility directory for reusable functions."""
        utilities = []
        
        for root, dirs, files in os.walk(dir_path):
            # Skip hidden directories and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.go', '.java')):
                    file_path = os.path.join(root, file)
                    functions = self.extract_functions(file_path)
                    if functions:
                        utilities.append({
                            "name": os.path.splitext(file)[0],
                            "path": file_path,
                            "functions": functions,
                            "purpose": self.infer_purpose(file, functions)
                        })
        
        return utilities

    def extract_functions(self, file_path: str) -> List[str]:
        """Extract function signatures from a file."""
        functions = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line in lines:
                    # Python functions
                    if line.strip().startswith('def ') and '(' in line:
                        func_name = line.strip().split('def ')[1].split('(')[0]
                        functions.append(func_name)
                    # JavaScript/TypeScript functions
                    elif 'function ' in line and '(' in line:
                        parts = line.split('function ')
                        if len(parts) > 1:
                            func_name = parts[1].split('(')[0].strip()
                            if func_name:
                                functions.append(func_name)
                    # Arrow functions and method definitions
                    elif ' = (' in line or ' => ' in line:
                        if 'const ' in line or 'let ' in line or 'var ' in line:
                            for keyword in ['const ', 'let ', 'var ']:
                                if keyword in line:
                                    func_name = line.split(keyword)[1].split('=')[0].strip()
                                    if func_name and not ' ' in func_name:
                                        functions.append(func_name)
                                    break
                    # Go functions
                    elif line.strip().startswith('func ') and '(' in line:
                        func_name = line.strip().split('func ')[1].split('(')[0]
                        functions.append(func_name)
                    # Java methods
                    elif ('public ' in line or 'private ' in line or 'protected ' in line) and '(' in line and ')' in line:
                        # Extract method name from Java method signature
                        parts = line.strip().split('(')[0].split()
                        if len(parts) >= 2:
                            func_name = parts[-1]
                            if func_name and not func_name in ['public', 'private', 'protected', 'static', 'void']:
                                functions.append(func_name)
        except:
            pass
        
        return functions[:15]  # Limit to top 15 functions

    def infer_purpose(self, filename: str, functions: List[str]) -> str:
        """Infer the purpose of a utility file based on its name and functions."""
        filename_lower = filename.lower()
        
        # Common patterns
        if 'email' in filename_lower or any('email' in f.lower() or 'mail' in f.lower() for f in functions):
            return "Email handling and sending"
        elif 'auth' in filename_lower or any('auth' in f.lower() or 'login' in f.lower() for f in functions):
            return "Authentication and authorization"
        elif 'crypto' in filename_lower or 'hash' in filename_lower or any('hash' in f.lower() or 'encrypt' in f.lower() for f in functions):
            return "Cryptography and hashing"
        elif 'token' in filename_lower or any('token' in f.lower() for f in functions):
            return "Token generation and validation"
        elif 'valid' in filename_lower or any('valid' in f.lower() or 'check' in f.lower() for f in functions):
            return "Input validation"
        elif 'date' in filename_lower or 'time' in filename_lower:
            return "Date and time utilities"
        elif 'string' in filename_lower or 'text' in filename_lower:
            return "String manipulation"
        elif 'file' in filename_lower or any('read' in f.lower() or 'write' in f.lower() for f in functions):
            return "File operations"
        elif 'http' in filename_lower or 'request' in filename_lower:
            return "HTTP requests and responses"
        elif 'db' in filename_lower or 'database' in filename_lower or 'query' in filename_lower:
            return "Database operations"
        elif 'cache' in filename_lower:
            return "Caching operations"
        elif 'log' in filename_lower:
            return "Logging utilities"
        elif 'error' in filename_lower or 'exception' in filename_lower:
            return "Error handling"
        elif 'response' in filename_lower:
            return "Response formatting"
        elif 'helper' in filename_lower:
            return "General helper functions"
        else:
            return "Utility functions"

    def generate_suggestions(self, results: Dict[str, Any]) -> str:
        """Generate implementation suggestions based on analysis."""
        suggestions = []

        # Based on patterns found
        if results.get("project_patterns"):
            patterns = results["project_patterns"]
            if patterns.get("service_layer"):
                suggestions.append("Create service class in services/ directory")
            if patterns.get("repository_pattern"):
                suggestions.append("Use repository pattern for data access")
            if patterns.get("mvc"):
                suggestions.append("Follow MVC pattern with models/views/controllers")
            if patterns.get("factory_pattern"):
                suggestions.append("Consider factory pattern for object creation")

        # Based on similar features
        if results.get("similar_features") and len(results["similar_features"]) > 0:
            similar = results["similar_features"][0]
            suggestions.append(f"Follow patterns from {similar['file']} ({similar['similarity']:.0%} similar)")

        # Based on utilities
        if results.get("utilities"):
            # Find relevant utilities based on task keywords
            task_words = self.task.lower().split()
            relevant_utils = []
            for util in results["utilities"]:
                util_name_lower = util["name"].lower()
                if any(word in util_name_lower for word in task_words if len(word) > 3):
                    relevant_utils.append(util)
                elif any(word in util.get("purpose", "").lower() for word in task_words if len(word) > 3):
                    relevant_utils.append(util)
            
            if relevant_utils:
                util = relevant_utils[0]
                suggestions.append(f"Reuse {util['name']} from {util['path']}")

        # Based on test framework
        if results.get("project_patterns", {}).get("test_framework"):
            framework = results["project_patterns"]["test_framework"]
            suggestions.append(f"Write tests using {framework}")

        return " | ".join(suggestions) if suggestions else "Implement following project conventions"

    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to JSON file."""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Analyze codebase for implementation context')
    parser.add_argument('--task', required=True, help='Task description')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--cache-enabled', action='store_true', help='Enable caching')
    parser.add_argument('--output', default='bazinga/codebase_analysis.json', help='Output file path')

    args = parser.parse_args()

    analyzer = CodebaseAnalyzer(
        task=args.task,
        session_id=args.session,
        cache_enabled=args.cache_enabled
    )

    try:
        results = analyzer.analyze()
        analyzer.save_results(results, args.output)
        
        print(f"Analysis complete. Results saved to {args.output}")
        print(f"Cache efficiency: {results['cache_efficiency']}")
        print(f"Found {len(results.get('similar_features', []))} similar features")
        print(f"Found {len(results.get('utilities', []))} utilities")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
