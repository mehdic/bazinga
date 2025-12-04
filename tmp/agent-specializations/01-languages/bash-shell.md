---
name: bash-shell
type: language
priority: 1
token_estimate: 350
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Bash/Shell Engineering Expertise

## Specialist Profile
Shell scripting specialist. Expert in POSIX compliance, error handling, and automation.

## Implementation Guidelines

### Script Header

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Script description
# Usage: script.sh [options] <args>

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
```

### Error Handling

```bash
error() {
    echo "ERROR: $*" >&2
    exit 1
}

warn() {
    echo "WARN: $*" >&2
}

cleanup() {
    # Cleanup on exit
    rm -rf "${TEMP_DIR:-}"
}
trap cleanup EXIT
```

### Argument Parsing

```bash
usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS] <input>

Options:
    -h, --help      Show this help
    -v, --verbose   Verbose output
    -o, --output    Output file
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) usage; exit 0 ;;
        -v|--verbose) VERBOSE=1; shift ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -*) error "Unknown option: $1" ;;
        *) INPUT="$1"; shift ;;
    esac
done

[[ -z "${INPUT:-}" ]] && error "Input required"
```

### Safe Variable Expansion

```bash
# Default values
name="${NAME:-default}"

# Required variables
: "${REQUIRED_VAR:?Variable REQUIRED_VAR must be set}"

# String operations
filename="${path##*/}"    # basename
dirname="${path%/*}"      # dirname
lowercase="${str,,}"
uppercase="${str^^}"
```

### Functions

```bash
process_file() {
    local file="$1"
    local output="${2:-/dev/stdout}"

    [[ -f "$file" ]] || { error "File not found: $file"; return 1; }

    # Process and output
    cat "$file" | transform > "$output"
}
```

## Patterns to Avoid
- ❌ Unquoted variables (`$var` instead of `"$var"`)
- ❌ `[ ]` instead of `[[ ]]`
- ❌ Parsing `ls` output
- ❌ Not checking command exit codes
- ❌ Hardcoded paths

## Verification Checklist
- [ ] `set -euo pipefail` at top
- [ ] All variables quoted
- [ ] Cleanup trap defined
- [ ] shellcheck passes
- [ ] Functions are local-scoped
