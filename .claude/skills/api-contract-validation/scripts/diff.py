#!/usr/bin/env python3
"""
OpenAPI Spec Diff

Compares two OpenAPI specs and detects breaking changes.
"""

from typing import List, Dict, Any, Set


def compare_specs(baseline: Dict, current: Dict) -> List[Dict[str, Any]]:
    """
    Compare two OpenAPI specs and detect changes.

    Args:
        baseline: Baseline (old) spec
        current: Current (new) spec

    Returns:
        List of changes detected
    """
    changes = []

    # Compare endpoints
    changes.extend(compare_paths(baseline, current))

    # Compare schemas/models
    changes.extend(compare_schemas(baseline, current))

    # Compare security requirements
    changes.extend(compare_security(baseline, current))

    return changes


def compare_paths(baseline: Dict, current: Dict) -> List[Dict[str, Any]]:
    """Compare API paths/endpoints."""
    changes = []

    baseline_paths = baseline.get('paths', {})
    current_paths = current.get('paths', {})

    # Check for removed endpoints
    for path, methods in baseline_paths.items():
        if path not in current_paths:
            changes.append({
                'type': 'endpoint_removed',
                'path': path,
                'methods': list(methods.keys()),
                'message': f"Endpoint removed: {path}"
            })
            continue

        # Check for removed methods
        for method, operation in methods.items():
            if method.lower() == 'parameters':  # Skip path-level parameters
                continue

            if method not in current_paths[path]:
                changes.append({
                    'type': 'method_removed',
                    'path': path,
                    'method': method.upper(),
                    'message': f"Method removed: {method.upper()} {path}"
                })
            else:
                # Compare operation details
                changes.extend(compare_operation(
                    baseline_paths[path][method],
                    current_paths[path][method],
                    path,
                    method
                ))

    # Check for added endpoints (safe change)
    for path, methods in current_paths.items():
        if path not in baseline_paths:
            changes.append({
                'type': 'endpoint_added',
                'path': path,
                'methods': list(methods.keys()),
                'message': f"New endpoint added: {path}"
            })

    return changes


def compare_operation(baseline_op: Dict, current_op: Dict, path: str, method: str) -> List[Dict]:
    """Compare a single operation (endpoint + method)."""
    changes = []

    # Compare parameters
    baseline_params = {p.get('name'): p for p in baseline_op.get('parameters', [])}
    current_params = {p.get('name'): p for p in current_op.get('parameters', [])}

    # Check for removed parameters
    for param_name, param in baseline_params.items():
        if param_name not in current_params:
            changes.append({
                'type': 'parameter_removed',
                'path': path,
                'method': method.upper(),
                'parameter': param_name,
                'was_required': param.get('required', False),
                'message': f"Parameter removed: {param_name} from {method.upper()} {path}"
            })
        else:
            # Check if parameter became required
            if not param.get('required', False) and current_params[param_name].get('required', False):
                changes.append({
                    'type': 'parameter_became_required',
                    'path': path,
                    'method': method.upper(),
                    'parameter': param_name,
                    'message': f"Parameter became required: {param_name} in {method.upper()} {path}"
                })

    # Check for added required parameters
    for param_name, param in current_params.items():
        if param_name not in baseline_params and param.get('required', False):
            changes.append({
                'type': 'required_parameter_added',
                'path': path,
                'method': method.upper(),
                'parameter': param_name,
                'message': f"New required parameter added: {param_name} to {method.upper()} {path}"
            })

    # Compare responses
    changes.extend(compare_responses(
        baseline_op.get('responses', {}),
        current_op.get('responses', {}),
        path,
        method
    ))

    # Compare request body
    if 'requestBody' in baseline_op or 'requestBody' in current_op:
        changes.extend(compare_request_body(
            baseline_op.get('requestBody', {}),
            current_op.get('requestBody', {}),
            path,
            method
        ))

    return changes


def compare_responses(baseline_responses: Dict, current_responses: Dict, path: str, method: str) -> List[Dict]:
    """Compare response definitions."""
    changes = []

    # Check for removed successful responses
    for status_code, response in baseline_responses.items():
        if status_code.startswith('2'):  # 2xx success codes
            if status_code not in current_responses:
                changes.append({
                    'type': 'response_status_removed',
                    'path': path,
                    'method': method.upper(),
                    'status_code': status_code,
                    'message': f"Response {status_code} removed from {method.upper()} {path}"
                })
            else:
                # Compare response schemas
                changes.extend(compare_response_schema(
                    response,
                    current_responses[status_code],
                    path,
                    method,
                    status_code
                ))

    return changes


def compare_response_schema(baseline_response: Dict, current_response: Dict, path: str, method: str, status: str) -> List[Dict]:
    """Compare response schema/structure."""
    changes = []

    # Get schema from response
    baseline_schema = get_schema_from_response(baseline_response)
    current_schema = get_schema_from_response(current_response)

    if not baseline_schema or not current_schema:
        return changes

    # Compare properties
    baseline_props = baseline_schema.get('properties', {})
    current_props = current_schema.get('properties', {})
    baseline_required = set(baseline_schema.get('required', []))

    # Check for removed fields
    for field_name, field_schema in baseline_props.items():
        if field_name not in current_props:
            changes.append({
                'type': 'response_field_removed',
                'path': path,
                'method': method.upper(),
                'status_code': status,
                'field': field_name,
                'was_required': field_name in baseline_required,
                'message': f"Response field removed: {field_name} from {method.upper()} {path}"
            })
        else:
            # Check for type changes
            old_type = field_schema.get('type')
            new_type = current_props[field_name].get('type')

            if old_type and new_type and old_type != new_type:
                # Check if it's a safe widening (int -> number)
                if not (old_type == 'integer' and new_type == 'number'):
                    changes.append({
                        'type': 'response_field_type_changed',
                        'path': path,
                        'method': method.upper(),
                        'field': field_name,
                        'old_type': old_type,
                        'new_type': new_type,
                        'message': f"Field type changed: {field_name} ({old_type} → {new_type})"
                    })

    return changes


def compare_request_body(baseline_body: Dict, current_body: Dict, path: str, method: str) -> List[Dict]:
    """Compare request body schemas."""
    changes = []

    if not baseline_body and current_body:
        if current_body.get('required', False):
            changes.append({
                'type': 'request_body_required',
                'path': path,
                'method': method.upper(),
                'message': f"Request body now required for {method.upper()} {path}"
            })

    return changes


def compare_schemas(baseline: Dict, current: Dict) -> List[Dict]:
    """Compare schema definitions (models)."""
    changes = []

    # Extract schemas from different OpenAPI versions
    baseline_schemas = get_schemas(baseline)
    current_schemas = get_schemas(current)

    # Check for removed schemas
    for schema_name in baseline_schemas:
        if schema_name not in current_schemas:
            changes.append({
                'type': 'schema_removed',
                'schema': schema_name,
                'message': f"Schema removed: {schema_name}"
            })

    return changes


def compare_security(baseline: Dict, current: Dict) -> List[Dict]:
    """Compare security requirements."""
    changes = []

    baseline_security = baseline.get('security', [])
    current_security = current.get('security', [])

    # Check if authentication was added globally
    if not baseline_security and current_security:
        changes.append({
            'type': 'security_added',
            'message': "Authentication requirement added globally"
        })

    return changes


def get_schema_from_response(response: Dict) -> Dict:
    """Extract schema from response definition."""
    # OpenAPI 3.x
    content = response.get('content', {})
    for media_type, media_obj in content.items():
        if 'schema' in media_obj:
            return media_obj['schema']

    # OpenAPI 2.x (Swagger)
    if 'schema' in response:
        return response['schema']

    return {}


def get_schemas(spec: Dict) -> Dict:
    """Get schema definitions from spec."""
    # OpenAPI 3.x
    if 'components' in spec and 'schemas' in spec['components']:
        return spec['components']['schemas']

    # OpenAPI 2.x
    if 'definitions' in spec:
        return spec['definitions']

    return {}


def classify_change_severity(change: Dict, baseline: Dict, current: Dict) -> str:
    """
    Classify change severity.

    Returns:
        Severity: critical, high, medium, low
    """
    change_type = change.get('type')

    # Critical (deployment blockers)
    critical_types = [
        'endpoint_removed',
        'method_removed',
        'response_status_removed',
    ]

    if change_type in critical_types:
        return 'critical'

    # High (likely to break clients)
    high_types = [
        'response_field_removed',
        'parameter_removed',
        'required_parameter_added',
        'security_added',
        'response_field_type_changed',
    ]

    if change_type in high_types:
        # Special case: removing non-required field is medium
        if change_type == 'response_field_removed' and not change.get('was_required', False):
            return 'medium'

        # Special case: removing non-required parameter is medium
        if change_type == 'parameter_removed' and not change.get('was_required', False):
            return 'medium'

        return 'high'

    # Medium (might break clients)
    medium_types = [
        'parameter_became_required',
        'request_body_required',
        'schema_removed',
    ]

    if change_type in medium_types:
        return 'medium'

    # Low/safe changes
    safe_types = [
        'endpoint_added',
        'response_field_added',
    ]

    if change_type in safe_types:
        return 'safe'

    # Default to medium for unknown types
    return 'medium'


# Example usage
if __name__ == "__main__":
    # Test with sample specs
    baseline = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        },
                                        "required": ["id", "name", "email"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    current = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"}
                                        },
                                        "required": ["id", "name"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    changes = compare_specs(baseline, current)
    for change in changes:
        severity = classify_change_severity(change, baseline, current)
        print(f"[{severity.upper()}] {change['type']}: {change['message']}")
