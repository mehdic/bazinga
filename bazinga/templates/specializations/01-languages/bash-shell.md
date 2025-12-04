---
name: bash-shell
type: language
priority: 1
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Bash/Shell Engineering Expertise

## Specialist Profile
Shell scripting specialist. Expert in POSIX compliance, error handling, ShellCheck, and secure automation.

---

## Patterns to Follow

### Script Header (Strict Mode)
- **Shebang**: `#!/usr/bin/env bash` for portability
- **Strict mode**: `set -euo pipefail` always
- **IFS setting**: `IFS=$'\n\t'` for safer word splitting
- **Readonly constants**: `readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`

### Variable Handling
- **Always quote variables**: `"$var"` not `$var`
- **Default values**: `"${VAR:-default}"` for optional
- **Required values**: `"${VAR:?must be set}"` for mandatory
- **Local in functions**: `local var="value"` always
- **Readonly for constants**: `readonly CONFIG_PATH="/etc/app"`

### Conditional Expressions
- **`[[ ]]` over `[ ]`**: No word splitting, supports regex
- **`-n` for non-empty**: `[[ -n "$var" ]]`
- **`-z` for empty**: `[[ -z "$var" ]]`
- **File tests**: `-f` (file), `-d` (dir), `-e` (exists), `-r` (readable)
- **Command substitution**: `$(command)` not backticks

### Modern Bash Features
<!-- version: bash >= 4.0 -->
- **Associative arrays**: `declare -A map; map[key]=value`
- **Globstar**: `shopt -s globstar; for f in **/*.txt`
<!-- version: bash >= 4.2 -->
- **lastpipe**: `shopt -s lastpipe` to run last pipe command in current shell
- **Negative indices**: `${array[-1]}` for last element
<!-- version: bash >= 4.3 -->
- **Nameref**: `declare -n ref=var` for variable indirection
<!-- version: bash >= 4.4 -->
- **@Q expansion**: `${var@Q}` for quoted representation
<!-- version: bash >= 5.0 -->
- **EPOCHSECONDS**: Built-in epoch time variable
- **wait -p**: Get PID of completed background job

### Error Handling
- **Trap for cleanup**: `trap cleanup EXIT`
- **Error to stderr**: `echo "Error: $msg" >&2`
- **Exit codes**: Non-zero for failure, specific codes for specific errors
- **Check command success**: `if ! command; then handle_error; fi`

### Functions
- **Local variables**: All function variables should be `local`
- **Return values**: Use `echo` for output, return code for success/failure
- **Guard clauses**: Check preconditions early
- **Single purpose**: One function, one job

### Security
- **Validate input**: Sanitize before use
- **No eval**: Avoid `eval` entirely
- **Quote expansions**: Prevent injection
- **Principle of least privilege**: Don't run as root unnecessarily

---

## Patterns to Avoid

### Quoting Errors
- ❌ **Unquoted variables**: `$var` instead of `"$var"` causes word splitting
- ❌ **Unquoted command substitution**: `$(cmd)` should be `"$(cmd)"`
- ❌ **Unquoted globs in conditions**: `[[ -f $file ]]` should quote `"$file"`

### Dangerous Constructs
- ❌ **`eval`**: Command injection risk; find alternatives
- ❌ **Backticks**: Use `$(command)` - clearer, nestable
- ❌ **`[ ]` instead of `[[ ]]`**: `[[ ]]` is safer and more powerful
- ❌ **Parsing `ls` output**: Use globs: `for f in *.txt`
- ❌ **`cat file | command`**: Use `command < file` or `command file`

### Error Handling Gaps
- ❌ **Missing `set -e`**: Commands fail silently
- ❌ **Missing `set -u`**: Undefined variables expand to empty
- ❌ **Missing `set -o pipefail`**: Pipeline errors hidden
- ❌ **No cleanup trap**: Resources left behind on error
- ❌ **Ignoring exit codes**: Always check `$?` or use `if`

### Portability Issues
- ❌ **Bashisms in /bin/sh**: Use bash if you need bash features
- ❌ **Hardcoded paths**: Use `$HOME`, `$(dirname "$0")`, etc.
- ❌ **Assuming tools exist**: Check with `command -v tool`

### Script Size
- ❌ **Scripts over 50 lines**: Google recommends keeping under 50
- ❌ **Complex logic in shell**: Consider Python for complexity

---

## Verification Checklist

### Strict Mode
- [ ] `#!/usr/bin/env bash` shebang
- [ ] `set -euo pipefail` at top
- [ ] Cleanup trap defined (`trap cleanup EXIT`)
- [ ] Script under 50 lines (or justified)

### Variables
- [ ] All variables quoted
- [ ] `local` used in functions
- [ ] `readonly` for constants
- [ ] Defaults with `${VAR:-default}`

### Safety
- [ ] ShellCheck passes (SC1000+)
- [ ] No `eval` usage
- [ ] Input validated
- [ ] Errors go to stderr

### Portability
- [ ] Works with bash 4+
- [ ] No hardcoded paths
- [ ] Dependencies checked with `command -v`
- [ ] Long options used (`--verbose` not `-v`)

---

## Code Patterns (Reference)

### Recommended Constructs
- **Strict header**: `#!/usr/bin/env bash; set -euo pipefail`
- **Readonly**: `readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
- **Default value**: `name="${NAME:-default}"`
- **Required value**: `: "${API_KEY:?API_KEY must be set}"`
- **Condition**: `[[ -f "$file" ]] && process "$file"`
- **Trap**: `trap 'rm -f "$tmpfile"' EXIT`
- **Function**: `func() { local arg="$1"; ... }`
- **Error**: `die() { echo "ERROR: $*" >&2; exit 1; }`
- **Loop**: `for file in *.txt; do process "$file"; done`
<!-- version: bash >= 4.0 -->
- **Assoc array**: `declare -A config; config[host]=localhost; echo "${config[host]}"`
- **Glob recursive**: `shopt -s globstar; for f in **/*.sh; do shellcheck "$f"; done`
<!-- version: bash >= 4.3 -->
- **Nameref**: `upvar() { declare -n ref="$1"; ref="$2"; }`
<!-- version: bash >= 5.0 -->
- **Epoch time**: `echo "Timestamp: $EPOCHSECONDS"`

