#!/usr/bin/env python3
"""
Codebase Analysis Skill - Main Script

Analyzes codebase to find similar features, reusable utilities, and patterns.

Usage:
    python analyze.py "Implement password reset endpoint"

Output:
    bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json
"""

import os
import sys
import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter
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
OUTPUT_FILE = OUTPUT_DIR / "codebase_analysis.json"

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
    from similarity import calculate_similarity, extract_keywords
    from patterns import detect_patterns, find_utilities, extract_conventions
except ImportError as e:
    # Graceful degradation if modules can't be imported
    if PROFILE == "lite":
        # Lite mode: Skip gracefully
        print(f"⚠️  Module import failed - codebase analysis skipped in lite mode")
        print(f"   Error: {e}")
        output = {
            "status": "skipped",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "impact": "Codebase analysis was skipped.",
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


def find_code_files(root_dir: str = ".", exclude_dirs: List[str] = None) -> List[str]:
    """
    Find all code files in the repository.

    Args:
        root_dir: Root directory to search
        exclude_dirs: Directories to exclude

    Returns:
        List of file paths
    """
    if exclude_dirs is None:
        exclude_dirs = [
            ".git", "node_modules", "venv", "__pycache__", ".pytest_cache",
            "build", "dist", ".next", ".cache", "bazinga", "docs"
        ]

    code_extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".rs",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt"
    }

    code_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            if Path(filename).suffix in code_extensions:
                filepath = os.path.join(dirpath, filename)
                code_files.append(filepath)

    return code_files


def find_similar_features(task_description: str, code_files: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Find files with similar functionality to the task.

    Args:
        task_description: Task description
        code_files: List of code files to search
        top_n: Number of similar files to return

    Returns:
        List of similar features with scores
    """
    # Extract keywords from task
    keywords = extract_keywords(task_description)

    similar_features = []

    for filepath in code_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Calculate similarity
            similarity_score = calculate_similarity(task_description, content)

            if similarity_score > 0.1:  # Threshold for relevance
                # Extract key functions/classes
                key_functions = extract_key_functions(content, filepath)

                # Detect patterns in file
                patterns = detect_file_patterns(content, filepath)

                similar_features.append({
                    "file": filepath,
                    "similarity_score": round(similarity_score, 2),
                    "patterns": patterns,
                    "key_functions": key_functions
                })
        except Exception as e:
            # Skip files that can't be read
            continue

    # Sort by similarity score and return top N
    similar_features.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_features[:top_n]


def extract_key_functions(content: str, filepath: str) -> List[str]:
    """
    Extract key function/class names from file content.

    Args:
        content: File content
        filepath: File path (for language detection)

    Returns:
        List of function/class names
    """
    functions = []

    # Python
    if filepath.endswith('.py'):
        # Match: def function_name(
        functions.extend(re.findall(r'def\s+(\w+)\s*\(', content))
        # Match: class ClassName
        functions.extend(re.findall(r'class\s+(\w+)', content))

    # JavaScript/TypeScript
    elif filepath.endswith(('.js', '.ts', '.tsx', '.jsx')):
        # Match: function functionName(
        functions.extend(re.findall(r'function\s+(\w+)\s*\(', content))
        # Match: const functionName = (
        functions.extend(re.findall(r'const\s+(\w+)\s*=\s*\(', content))
        # Match: class ClassName
        functions.extend(re.findall(r'class\s+(\w+)', content))
        # Match: export function functionName
        functions.extend(re.findall(r'export\s+function\s+(\w+)', content))

    # Go
    elif filepath.endswith('.go'):
        # Match: func FunctionName(
        functions.extend(re.findall(r'func\s+(\w+)\s*\(', content))
        # Match: func (r *Receiver) Method(
        functions.extend(re.findall(r'func\s+\([^)]+\)\s+(\w+)\s*\(', content))

    # Java
    elif filepath.endswith('.java'):
        # Match: public/private/protected Type methodName(
        functions.extend(re.findall(r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(', content))
        # Match: class ClassName
        functions.extend(re.findall(r'class\s+(\w+)', content))

    # Return unique functions, limit to 10
    return list(set(functions))[:10]


def detect_file_patterns(content: str, filepath: str) -> List[str]:
    """
    Detect patterns in a single file.

    Args:
        content: File content
        filepath: File path

    Returns:
        List of detected patterns
    """
    patterns = []

    # Service layer
    if 'service' in filepath.lower() or 'Service' in content:
        patterns.append("service layer")

    # Repository pattern
    if 'repository' in filepath.lower() or 'Repository' in content:
        patterns.append("repository pattern")

    # Factory pattern
    if 'factory' in filepath.lower() or 'Factory' in content or 'create' in content.lower():
        patterns.append("factory pattern")

    # Email functionality
    if 'email' in content.lower():
        patterns.append("email functionality")

    # Token generation
    if 'token' in content.lower():
        patterns.append("token generation")

    # Validation
    if 'valid' in content.lower() or 'validate' in content.lower():
        patterns.append("validation")

    # Error handling
    if 'error' in content.lower() or 'exception' in content.lower():
        patterns.append("error handling")

    # Authentication
    if 'auth' in content.lower():
        patterns.append("authentication")

    return patterns


def analyze_codebase(task_description: str) -> Dict[str, Any]:
    """
    Main analysis function.

    Args:
        task_description: Task to implement

    Returns:
        Analysis results as dictionary
    """
    print(f"🔍 Analyzing codebase for: {task_description}")

    # Step 1: Find all code files
    print("📁 Finding code files...")
    code_files = find_code_files()
    print(f"   Found {len(code_files)} code files")

    # Step 2: Find similar features
    print("🔎 Finding similar features...")
    similar_features = find_similar_features(task_description, code_files)
    print(f"   Found {len(similar_features)} similar features")

    # Step 3: Find reusable utilities
    print("🛠️  Finding reusable utilities...")
    reusable_utilities = find_utilities()
    print(f"   Found {len(reusable_utilities)} utilities")

    # Step 4: Detect architectural patterns
    print("🏗️  Detecting architectural patterns...")
    architectural_patterns = detect_patterns()
    print(f"   Found {len(architectural_patterns)} patterns")

    # Step 5: Extract conventions
    print("📋 Extracting project conventions...")
    conventions = extract_conventions()
    print(f"   Found {len(conventions)} conventions")

    # Step 6: Generate suggested approach
    print("💡 Generating suggested approach...")
    suggested_approach = generate_suggestion(
        task_description,
        similar_features,
        reusable_utilities,
        architectural_patterns
    )

    # Build result
    result = {
        "task": task_description,
        "similar_features": similar_features,
        "reusable_utilities": reusable_utilities,
        "architectural_patterns": architectural_patterns,
        "suggested_approach": suggested_approach,
        "conventions": conventions
    }

    return result


def generate_suggestion(
    task: str,
    similar_features: List[Dict],
    utilities: List[Dict],
    patterns: List[str]
) -> str:
    """
    Generate implementation suggestion based on analysis.

    Args:
        task: Task description
        similar_features: Similar features found
        utilities: Available utilities
        patterns: Architectural patterns

    Returns:
        Suggested implementation approach
    """
    suggestion_parts = []

    # Extract main action from task
    task_lower = task.lower()

    # Pattern suggestions
    if "service layer pattern" in patterns:
        if "implement" in task_lower:
            # Extract feature name
            feature = task.split("implement")[-1].strip()
            service_name = feature.title().replace(" ", "") + "Service"
            suggestion_parts.append(f"Create {service_name} in services/")

    # Utility suggestions
    if utilities:
        utility_names = [u["name"] for u in utilities[:3]]
        if len(utility_names) > 0:
            suggestion_parts.append(f"use existing {', '.join(utility_names)}")

    # Similar feature suggestions
    if similar_features:
        top_similar = similar_features[0]
        suggestion_parts.append(f"follow patterns from {top_similar['file']}")

    # Combine suggestions
    if suggestion_parts:
        return "; ".join(suggestion_parts)
    else:
        return "Implement following existing project structure and conventions"


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze.py \"Task description\"")
        sys.exit(1)

    task_description = sys.argv[1]

    # Run analysis
    result = analyze_codebase(task_description)

    # Write output to session artifacts directory
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Analysis complete! Results written to: {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"   - Similar features: {len(result['similar_features'])}")
    print(f"   - Reusable utilities: {len(result['reusable_utilities'])}")
    print(f"   - Patterns detected: {len(result['architectural_patterns'])}")
    print(f"   - Conventions: {len(result['conventions'])}")
    print(f"\n💡 Suggestion: {result['suggested_approach']}")


if __name__ == "__main__":
    main()
