---
name: api-contract-validation
description: Detect breaking changes in API contracts (OpenAPI/Swagger specs)
allowed-tools: [Bash, Read, Write, Grep]
---

# API Contract Validation Skill

You are the api-contract-validation skill. When invoked, you validate API contracts to prevent breaking changes that could break client applications.

## Your Task

When invoked, you will:
1. Find OpenAPI/Swagger specification files
2. Load baseline (previous version) for comparison
3. Compare specs to detect breaking changes
4. Identify safe changes
5. Generate recommendations
6. Generate structured report

---

## Step 1: Find OpenAPI Specs

Use **Bash** to search for OpenAPI/Swagger files:

```bash
find . -name "openapi.yaml" -o -name "openapi.json" -o -name "swagger.yaml" -o -name "swagger.json" -o -name "api.yaml" | head -5
```

If not found, check for auto-generation from frameworks:

**FastAPI (Python):**
```bash
# Check if FastAPI is used
grep -r "from fastapi import" --include="*.py" -l | head -1
# If found, generate spec:
# python -c "from main import app; import json; print(json.dumps(app.openapi()))" > openapi.json
```

**Express (Node.js):**
```bash
grep -r "swagger-jsdoc\|swagger-ui-express" package.json
```

---

## Step 2: Load Current and Baseline Specs

Use the **Read** tool to:
1. Read current spec file
2. Read `coordination/api_baseline.json` (if exists)

**If baseline doesn't exist:**
- This is first run
- Save current spec as baseline for future comparisons
- Return: "Baseline created. Run again after API changes to detect breaking changes."

---

## Step 3: Compare Specs for Breaking Changes

**CRITICAL breaking changes:**

1. **Endpoint removed:**
```
if path exists in baseline but not in current:
    breaking_change = "Endpoint {path} removed - clients may break"
```

2. **Required parameter removed:**
```
if required param in baseline but not in current:
    breaking_change = "Required parameter {param} removed from {endpoint}"
```

3. **Response field removed:**
```
if field in baseline response schema but not in current:
    breaking_change = "Response field {field} removed from {endpoint}"
```

4. **Response status code changed:**
```
if success status changed (e.g., 200 → 404):
    breaking_change = "Status code changed for {endpoint}"
```

**HIGH severity:**

5. **Field type changed (incompatible):**
```
if field type changed (e.g., string → integer):
    breaking_change = "Field {field} type changed from {old} to {new}"
```

6. **Required parameter added:**
```
if new required param added:
    breaking_change = "New required parameter {param} added to {endpoint}"
```

7. **Enum values removed:**
```
if enum values exist in baseline but not current:
    breaking_change = "Enum values removed from {field}"
```

**SAFE changes:**

- New endpoint added
- Optional parameter added
- Optional response field added
- Enum values added
- Documentation updated

---

## Step 4: Detect Field Type Changes

For each field in responses:

```
if baseline_type == "integer" and current_type == "number":
    # Widening (int → float) - potentially safe
    warning = "Field type widened (safe if clients handle floats)"

elif baseline_type == "number" and current_type == "integer":
    # Narrowing - breaking
    breaking = "Field type narrowed (breaks clients expecting floats)"
```

---

## Step 5: Generate Recommendations

For each breaking change, suggest alternatives:

**If endpoint removed:**
- "Consider API versioning (/v2/endpoint) instead of removal"
- "Deprecate with 410 Gone status before removing"

**If field removed:**
- "Add field back or create new versioned endpoint"
- "Deprecate field first with warning, remove in v2"

**If required param added:**
- "Make parameter optional with default value"
- "Create new endpoint version with new parameter"

---

## Step 6: Write Output

Use the **Write** tool to create `coordination/api_contract_validation.json`:

```json
{
  "status": "breaking_changes_detected|safe|no_baseline",
  "specs_found": ["<spec file 1>"],
  "baseline_exists": true|false,
  "breaking_changes": [
    {
      "severity": "critical|high",
      "type": "endpoint_removed|field_removed|type_changed|...",
      "path": "<API path>",
      "method": "<HTTP method>",
      "field": "<field name>",
      "message": "<description>",
      "old_value": "<baseline value>",
      "new_value": "<current value>"
    }
  ],
  "warnings": [
    {
      "severity": "medium",
      "type": "field_type_widened|...",
      "path": "<API path>",
      "message": "<description>"
    }
  ],
  "safe_changes": [
    {
      "type": "endpoint_added|field_added|...",
      "path": "<API path>",
      "message": "<description>"
    }
  ],
  "recommendations": [
    "<recommendation 1>",
    "<recommendation 2>"
  ]
}
```

Also update `coordination/api_baseline.json` with current spec for next comparison.

---

## Step 7: Return Summary

Return a concise summary:

```
API Contract Validation:
- Specs analyzed: X
- Baseline: {exists/created}

⚠️  BREAKING CHANGES: Y
- Critical: X
- High: Y

Safe changes: Z

{If breaking changes:}
Top recommendations:
1. <recommendation 1>
2. <recommendation 2>

Details saved to: coordination/api_contract_validation.json
```

---

## Error Handling

**If no specs found:**
- Return: "No OpenAPI/Swagger specs found. Cannot validate API contracts."

**If spec parsing fails:**
- Return: "Failed to parse spec: {error}. Check spec format."

**If no baseline:**
- Create baseline from current spec
- Return: "Baseline created for future comparisons."

---

## Notes

- **Endpoint removal** is CRITICAL (breaks existing clients)
- **Field removal** from responses is HIGH severity
- **Adding optional fields** is safe
- **Type widening** (int → float) may be safe depending on clients
- Always suggest **versioning** over breaking changes
