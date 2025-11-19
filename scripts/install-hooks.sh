#!/bin/bash
#
# Install git hooks for BAZINGA development
# Run this after cloning the repository
#

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔧 Installing git hooks for BAZINGA development..."

# Install pre-commit hook
if [ -f scripts/git-hooks/pre-commit ]; then
    cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "  ✅ Pre-commit hook installed"
else
    echo "  ❌ ERROR: Hook template not found at scripts/git-hooks/pre-commit"
    exit 1
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will automatically:"
echo "  - Detect changes to agents/orchestrator.md"
echo "  - Validate §line and §Step references"
echo "  - Rebuild .claude/commands/bazinga.orchestrate.md"
echo "  - Stage the generated file"
echo ""
