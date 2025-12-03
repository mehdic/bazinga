#!/usr/bin/env python3
"""
API Contract Validation Skill - Main Script

Detects breaking changes in OpenAPI/Swagger specifications.

Usage:
    python validate.py

Output:
    bazinga/artifacts/{SESSION_ID}/skills/api_contract_validation.json
"""

import os
import sys
import json
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
OUTPUT_FILE = OUTPUT_DIR / "api_contract_validation.json"

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
    from parser import find_openapi_specs, parse_spec, auto_generate_spec
    from diff import compare_specs, classify_change_severity
except ImportError as e:
    # Graceful degradation if modules can't be imported
    if PROFILE == "lite":
        # Lite mode: Skip gracefully
        print(f"⚠️  Module import failed - API contract validation skipped in lite mode")
        print(f"   Error: {e}")
        output = {
            "status": "skipped",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "impact": "API contract validation was skipped. You can manually review OpenAPI specs for breaking changes.",
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


def find_baseline(coordination_dir: str = "bazinga") -> Optional[Dict]:
    """
    Find baseline API spec from previous run.

    Args:
        coordination_dir: Coordination directory

    Returns:
        Baseline spec or None if first run
    """
    baseline_path = os.path.join(coordination_dir, "api_baseline.json")

    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load baseline: {e}")
            return None

    return None


def save_baseline(spec: Dict, coordination_dir: str = "bazinga"):
    """
    Save current spec as baseline for future comparisons.

    Args:
        spec: OpenAPI specification
        coordination_dir: Coordination directory
    """
    os.makedirs(coordination_dir, exist_ok=True)
    baseline_path = os.path.join(coordination_dir, "api_baseline.json")

    with open(baseline_path, 'w') as f:
        json.dump(spec, f, indent=2)


def validate_api_contract() -> Dict[str, Any]:
    """
    Main validation function.

    Returns:
        Validation results as dictionary
    """
    print("🔍 API Contract Validation")
    print("=" * 50)

    # Step 1: Find OpenAPI specs
    print("\n📁 Finding OpenAPI specifications...")
    spec_files = find_openapi_specs()

    if not spec_files:
        # Try auto-generation from frameworks
        print("   No OpenAPI files found, attempting auto-generation...")
        spec_file = auto_generate_spec()

        if spec_file:
            spec_files = [spec_file]
            print(f"   ✅ Generated spec from framework: {spec_file}")
        else:
            return {
                "status": "no_specs_found",
                "message": "No OpenAPI specifications found and could not auto-generate",
                "recommendation": "Add openapi.yaml or use a framework with auto-generation (FastAPI, Flask-RESTX, Express with swagger-jsdoc)"
            }
    else:
        print(f"   Found {len(spec_files)} spec file(s):")
        for spec_file in spec_files:
            print(f"     - {spec_file}")

    # Step 2: Parse current spec
    print("\n📄 Parsing current specification...")
    current_spec_file = spec_files[0]  # Use first spec found
    current_spec = parse_spec(current_spec_file)

    if not current_spec:
        return {
            "status": "parse_error",
            "message": f"Failed to parse {current_spec_file}",
            "recommendation": "Check spec syntax with validator: https://editor.swagger.io/"
        }

    print(f"   ✅ Parsed successfully")
    print(f"   Spec version: {current_spec.get('openapi') or current_spec.get('swagger')}")
    print(f"   Endpoints: {sum(len(methods) for methods in current_spec.get('paths', {}).values())}")

    # Step 3: Load baseline
    print("\n📊 Loading baseline specification...")
    baseline_spec = find_baseline()

    if not baseline_spec:
        print("   No baseline found - this is the first run")
        save_baseline(current_spec)
        return {
            "status": "baseline_created",
            "message": "Baseline API spec created for future comparisons",
            "spec_file": current_spec_file,
            "endpoints": sum(len(methods) for methods in current_spec.get('paths', {}).values())
        }

    print("   ✅ Baseline loaded")

    # Step 4: Compare specs
    print("\n🔎 Comparing specifications...")
    changes = compare_specs(baseline_spec, current_spec)

    print(f"   Found {len(changes)} change(s)")

    # Step 5: Classify changes
    print("\n⚖️  Classifying changes by severity...")
    breaking_changes = []
    warnings = []
    safe_changes = []

    for change in changes:
        severity = classify_change_severity(change, baseline_spec, current_spec)
        change['severity'] = severity

        if severity in ['critical', 'high']:
            breaking_changes.append(change)
        elif severity == 'medium':
            warnings.append(change)
        else:
            safe_changes.append(change)

    print(f"   Breaking changes: {len(breaking_changes)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Safe changes: {len(safe_changes)}")

    # Step 6: Generate recommendations
    print("\n💡 Generating recommendations...")
    recommendations = generate_recommendations(breaking_changes)

    # Step 7: Update baseline
    save_baseline(current_spec)
    print("\n✅ Baseline updated")

    # Build result
    result = {
        "status": "breaking_changes_detected" if breaking_changes else "safe_changes_only",
        "specs_found": spec_files,
        "baseline_exists": True,
        "breaking_changes": breaking_changes,
        "warnings": warnings,
        "safe_changes": safe_changes,
        "recommendations": recommendations
    }

    return result


def generate_recommendations(breaking_changes: List[Dict]) -> List[str]:
    """
    Generate recommendations based on breaking changes.

    Args:
        breaking_changes: List of breaking changes

    Returns:
        List of recommendation strings
    """
    recommendations = []

    for change in breaking_changes:
        if change['type'] == 'endpoint_removed':
            path = change.get('path', '')
            recommendations.append(
                f"Consider API versioning (e.g., /v2{path}) instead of removing {change.get('method', 'GET')} {path}"
            )
            recommendations.append(
                f"Alternatively, deprecate endpoint with 410 Gone status before complete removal"
            )

        elif change['type'] == 'response_field_removed':
            field = change.get('field', '')
            recommendations.append(
                f"Add '{field}' field back or create new versioned endpoint"
            )

        elif change['type'] == 'request_parameter_required':
            param = change.get('parameter', '')
            recommendations.append(
                f"Make parameter '{param}' optional with sensible default value"
            )

        elif change['type'] == 'response_type_changed':
            field = change.get('field', '')
            old_type = change.get('old_type', '')
            new_type = change.get('new_type', '')
            recommendations.append(
                f"Field '{field}' type change ({old_type} → {new_type}) will break clients - version the endpoint"
            )

    # Remove duplicates
    recommendations = list(dict.fromkeys(recommendations))

    # Add general recommendation if breaking changes exist
    if breaking_changes:
        recommendations.insert(0, "CRITICAL: Deploy breaking changes as new API version (/v2) to maintain backward compatibility")

    return recommendations


def main():
    """Main entry point."""
    # Run validation
    result = validate_api_contract()

    # Write output to session artifacts directory
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ Validation complete!")
    print(f"📄 Results: {OUTPUT_FILE}")

    # Print summary
    status = result.get('status')
    if status == 'baseline_created':
        print(f"\n📊 Status: Baseline created (first run)")
    elif status == 'no_specs_found':
        print(f"\n❌ Status: No OpenAPI specs found")
    elif status == 'breaking_changes_detected':
        print(f"\n⚠️  Status: BREAKING CHANGES DETECTED")
        print(f"   - Breaking: {len(result.get('breaking_changes', []))}")
        print(f"   - Warnings: {len(result.get('warnings', []))}")
        print(f"\n💡 Top recommendation:")
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"   {recommendations[0]}")
    elif status == 'safe_changes_only':
        print(f"\n✅ Status: All changes are backward compatible")
        print(f"   - Safe changes: {len(result.get('safe_changes', []))}")

    # Exit with error code if breaking changes
    if status == 'breaking_changes_detected':
        sys.exit(1)


if __name__ == "__main__":
    main()
