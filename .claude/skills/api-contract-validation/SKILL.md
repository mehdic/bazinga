# API Contract Validation Skill

**Type:** Model-invoked API validation tool
**Purpose:** Detect breaking changes in API contracts (OpenAPI/Swagger specs)
**Complexity:** Medium (5-15 seconds runtime)

## What This Skill Does

Before deploying API changes, this Skill validates API contracts to prevent breaking changes that could break client applications.

**Key Capabilities:**
1. **Breaking Change Detection**: Identifies removed endpoints, changed response types, removed fields
2. **OpenAPI/Swagger Support**: Parses OpenAPI 2.0, 3.0, 3.1 specs (JSON/YAML)
3. **Baseline Comparison**: Compares new spec against previous version
4. **Safe Change Validation**: Ensures backward compatibility
5. **Multi-Framework**: Detects specs from FastAPI, Flask, Express, Django, Spring Boot

## Usage

```bash
/api-contract-validation
```

The Skill automatically finds OpenAPI specs in common locations:
- `openapi.yaml`, `openapi.json`
- `swagger.yaml`, `swagger.json`
- `docs/api/openapi.yaml`
- Auto-generated from FastAPI, Flask-RESTX, Express

## Output

**File:** `coordination/api_contract_validation.json`

```json
{
  "status": "breaking_changes_detected",
  "specs_found": ["openapi.yaml"],
  "baseline_exists": true,
  "breaking_changes": [
    {
      "severity": "critical",
      "type": "endpoint_removed",
      "path": "/api/users/{id}",
      "method": "DELETE",
      "message": "Endpoint removed - clients may break"
    },
    {
      "severity": "high",
      "type": "response_field_removed",
      "path": "/api/users",
      "method": "GET",
      "field": "user.email",
      "message": "Required response field removed"
    }
  ],
  "warnings": [
    {
      "severity": "medium",
      "type": "field_type_changed",
      "path": "/api/orders",
      "field": "total",
      "old_type": "integer",
      "new_type": "number",
      "message": "Field type widened (safe if clients handle floats)"
    }
  ],
  "safe_changes": [
    {
      "type": "endpoint_added",
      "path": "/api/health",
      "method": "GET",
      "message": "New endpoint added (backward compatible)"
    },
    {
      "type": "response_field_added",
      "path": "/api/users",
      "field": "user.created_at",
      "message": "New optional field added"
    }
  ],
  "recommendations": [
    "Consider versioning API (/v2/users) instead of removing /api/users/{id}",
    "Deprecate endpoint with 410 Gone status before complete removal",
    "Add email field back or version the endpoint"
  ]
}
```

## Breaking Changes Detected

**Critical (deployment blockers):**
- Endpoint removed
- Required request parameter removed
- Required response field removed
- Response status code changed (200 → 404)
- Authentication requirement added

**High (likely to break clients):**
- Response field type changed (incompatible)
- Required parameter added
- Enum values removed
- Error response format changed

**Medium (might break clients):**
- Optional field type widened (int → float)
- New validation rules (stricter)
- Response field deprecated
- Default values changed

**Safe Changes:**
- New endpoint added
- Optional response field added
- Optional parameter added
- Documentation updated
- Enum values added

## How It Works

### Step 1: Find OpenAPI Specs

Search for OpenAPI/Swagger files:
```python
# Common locations
spec_paths = [
    "openapi.yaml", "openapi.json",
    "swagger.yaml", "swagger.json",
    "docs/api/openapi.yaml",
    "api/openapi.yaml"
]

# Auto-generate from frameworks
if has_fastapi:
    run: "python -c 'from main import app; import json; print(json.dumps(app.openapi()))' > openapi.json"
```

### Step 2: Load Baseline (Previous Version)

```python
# Check coordination/ for previous spec
baseline_path = "coordination/api_baseline.json"
if exists(baseline_path):
    baseline_spec = load_json(baseline_path)
else:
    # First run - save current as baseline
    save_json(baseline_path, current_spec)
    return {"status": "baseline_created"}
```

### Step 3: Compare Specs

```python
breaking_changes = []

# Check for removed endpoints
for path, methods in baseline_spec["paths"].items():
    if path not in current_spec["paths"]:
        breaking_changes.append({
            "severity": "critical",
            "type": "endpoint_removed",
            "path": path
        })

# Check for removed response fields
for path, methods in current_spec["paths"].items():
    for method, operation in methods.items():
        baseline_schema = get_response_schema(baseline_spec, path, method)
        current_schema = get_response_schema(current_spec, path, method)

        removed_fields = find_removed_fields(baseline_schema, current_schema)
        for field in removed_fields:
            breaking_changes.append({
                "severity": "high",
                "type": "response_field_removed",
                "field": field
            })
```

### Step 4: Generate Recommendations

```python
recommendations = []

for change in breaking_changes:
    if change["type"] == "endpoint_removed":
        recommendations.append(
            f"Consider API versioning (/v2{change['path']}) instead of removal"
        )
    elif change["type"] == "response_field_removed":
        recommendations.append(
            f"Add field back or create new versioned endpoint"
        )
```

## Implementation

**Files:**
- `validate.py`: Main validation orchestrator
- `parser.py`: OpenAPI spec parser (YAML/JSON)
- `diff.py`: Spec comparison and breaking change detection
- `frameworks.py`: Auto-detection and spec generation

**Dependencies:**
- Python 3.8+
- PyYAML (for YAML parsing)
- jsonschema (for schema validation)

**Runtime:** 5-15 seconds depending on spec size

**Languages Supported:** Any (analyzes OpenAPI specs, not code)

## When to Use

✅ **Use this Skill when:**
- Making changes to API endpoints
- Modifying request/response schemas
- Before deploying API updates
- In CI/CD pipeline for API changes

❌ **Don't use when:**
- No OpenAPI spec exists
- Creating brand new API (no baseline)
- Non-REST APIs (GraphQL, gRPC - different validation)

## Example Workflow

```bash
# Developer modifies API endpoint
# Developer ready to commit

# Developer invokes Skill
/api-contract-validation

# Skill analyzes API spec (5-15 seconds)
# Compares against baseline
# Detects breaking changes

# Developer sees:
# - CRITICAL: Removed /api/users/{id} DELETE endpoint
# - Recommendation: Use API versioning instead

# Developer fixes:
# - Adds /v2/api/users with new behavior
# - Keeps /v1/api/users/{id} DELETE for backward compat
# - Updates clients to use v2

# Re-run validation
/api-contract-validation
# Result: All safe changes ✅
```

## Benefits

**Without Skill:**
- Developer removes endpoint → deploys
- Client apps break in production
- Emergency rollback required
- Customer complaints
- **Total:** 2-4 hours incident response

**With Skill:**
- Skill detects breaking change (10 seconds)
- Developer versions API instead
- Smooth deployment, no breakage
- **Total:** 20 minutes to implement versioning

**ROI:** 6-12x (prevents production incidents)

## Integration

This Skill is available in:
- **Superpowers Mode**: Developer must check before committing API changes
- **Standard Mode**: Not available (time-sensitive)

Orchestrator injects this Skill into Developer prompt when superpowers mode is active and API changes are detected.
