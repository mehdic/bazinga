#!/usr/bin/env python3
"""
OpenAPI Spec Parser

Finds and parses OpenAPI/Swagger specifications.
"""

import os
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None


def find_openapi_specs() -> List[str]:
    """
    Find OpenAPI spec files in common locations.

    Returns:
        List of spec file paths
    """
    spec_files = []

    # Common file names and locations
    common_paths = [
        "openapi.yaml",
        "openapi.json",
        "openapi.yml",
        "swagger.yaml",
        "swagger.json",
        "swagger.yml",
        "api/openapi.yaml",
        "api/swagger.yaml",
        "docs/openapi.yaml",
        "docs/api/openapi.yaml",
        "docs/swagger.yaml",
        "spec/openapi.yaml",
        "spec/swagger.yaml",
    ]

    for path in common_paths:
        if os.path.exists(path):
            spec_files.append(path)

    return spec_files


def parse_spec(spec_file: str) -> Optional[Dict]:
    """
    Parse OpenAPI spec file (YAML or JSON).

    Args:
        spec_file: Path to spec file

    Returns:
        Parsed spec dictionary or None on error
    """
    try:
        with open(spec_file, 'r') as f:
            content = f.read()

        # Try JSON first
        if spec_file.endswith('.json'):
            return json.loads(content)

        # Try YAML
        if spec_file.endswith(('.yaml', '.yml')):
            if yaml:
                return yaml.safe_load(content)
            else:
                # Try to parse as JSON (YAML is superset of JSON)
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    print("⚠️  YAML file found but PyYAML not installed")
                    print("   Install with: pip install PyYAML")
                    return None

    except Exception as e:
        print(f"Error parsing {spec_file}: {e}")
        return None


def auto_generate_spec() -> Optional[str]:
    """
    Attempt to auto-generate OpenAPI spec from framework.

    Returns:
        Path to generated spec or None
    """
    # Try FastAPI
    if os.path.exists("main.py"):
        spec = try_fastapi_spec()
        if spec:
            return spec

    # Try Flask-RESTX / Flask-RESTPlus
    if os.path.exists("app.py") or os.path.exists("application.py"):
        spec = try_flask_spec()
        if spec:
            return spec

    # Try Django REST Framework
    if os.path.exists("manage.py"):
        spec = try_django_spec()
        if spec:
            return spec

    # Try Express with swagger-jsdoc
    if os.path.exists("package.json"):
        spec = try_express_spec()
        if spec:
            return spec

    return None


def try_fastapi_spec() -> Optional[str]:
    """Generate OpenAPI spec from FastAPI app."""
    try:
        # Try common FastAPI app locations
        app_files = ["main.py", "app.py", "api.py"]

        for app_file in app_files:
            if not os.path.exists(app_file):
                continue

            # Read file to find app variable name
            with open(app_file, 'r') as f:
                content = f.read()

            # Look for FastAPI() instantiation
            app_match = re.search(r'(\w+)\s*=\s*FastAPI\(', content)
            if not app_match:
                continue

            app_var = app_match.group(1)
            module = Path(app_file).stem

            # Generate spec
            cmd = f"python -c \"from {module} import {app_var}; import json; print(json.dumps({app_var}.openapi()))\""

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # Save generated spec
                with open("openapi.json", 'w') as f:
                    f.write(result.stdout)
                return "openapi.json"

    except Exception as e:
        print(f"   FastAPI generation failed: {e}")

    return None


def try_flask_spec() -> Optional[str]:
    """Generate OpenAPI spec from Flask-RESTX/RESTPlus app."""
    try:
        app_files = ["app.py", "application.py", "main.py"]

        for app_file in app_files:
            if not os.path.exists(app_file):
                continue

            with open(app_file, 'r') as f:
                content = f.read()

            # Check for Flask-RESTX or RESTPlus
            if 'flask_restx' not in content.lower() and 'flask_restplus' not in content.lower():
                continue

            # Look for Api() instantiation
            api_match = re.search(r'(\w+)\s*=\s*(?:Api|flask_restx\.Api|flask_restplus\.Api)\(', content)
            if not api_match:
                continue

            api_var = api_match.group(1)
            module = Path(app_file).stem

            # Generate spec
            cmd = f"python -c \"from {module} import {api_var}; import json; print(json.dumps({api_var}.__schema__))\""

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                with open("openapi.json", 'w') as f:
                    f.write(result.stdout)
                return "openapi.json"

    except Exception as e:
        print(f"   Flask generation failed: {e}")

    return None


def try_django_spec() -> Optional[str]:
    """Generate OpenAPI spec from Django REST Framework."""
    try:
        # Check if DRF is used
        if not os.path.exists("manage.py"):
            return None

        # Try using drf-spectacular or drf-yasg if installed
        cmd = "python manage.py spectacular --file openapi.yaml 2>/dev/null || python manage.py generateschema --file openapi.yaml 2>/dev/null"

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and os.path.exists("openapi.yaml"):
            return "openapi.yaml"

    except Exception as e:
        print(f"   Django generation failed: {e}")

    return None


def try_express_spec() -> Optional[str]:
    """Generate OpenAPI spec from Express with swagger-jsdoc."""
    try:
        # Check package.json for swagger dependencies
        with open("package.json", 'r') as f:
            package = json.load(f)

        dependencies = {**package.get('dependencies', {}), **package.get('devDependencies', {})}

        if 'swagger-jsdoc' not in dependencies and 'swagger-ui-express' not in dependencies:
            return None

        # Look for swagger config or generation script
        if os.path.exists("swagger.js") or os.path.exists("swagger.config.js"):
            # Try running swagger generation if there's a script
            scripts = package.get('scripts', {})
            for script_name, script_cmd in scripts.items():
                if 'swagger' in script_name.lower() or 'openapi' in script_name.lower():
                    result = subprocess.run(
                        f"npm run {script_name}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15
                    )

                    # Check if spec was generated
                    if os.path.exists("openapi.json") or os.path.exists("swagger.json"):
                        return "openapi.json" if os.path.exists("openapi.json") else "swagger.json"

    except Exception as e:
        print(f"   Express generation failed: {e}")

    return None


# Example usage
if __name__ == "__main__":
    print("Finding OpenAPI specs...")
    specs = find_openapi_specs()
    if specs:
        print(f"Found: {specs}")
        for spec_file in specs:
            parsed = parse_spec(spec_file)
            if parsed:
                print(f"Parsed {spec_file}: {parsed.get('info', {}).get('title', 'Unknown')}")
    else:
        print("No specs found, attempting auto-generation...")
        generated = auto_generate_spec()
        if generated:
            print(f"Generated: {generated}")
        else:
            print("Could not auto-generate spec")
