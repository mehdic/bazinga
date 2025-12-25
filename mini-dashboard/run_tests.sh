#!/bin/bash
# Run all mini-dashboard tests
#
# Usage:
#   ./run_tests.sh          # Run all tests
#   ./run_tests.sh api      # Run API tests only
#   ./run_tests.sh frontend # Run frontend tests only (requires playwright)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mini Dashboard Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Check for pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found. Install with: pip install pytest${NC}"
    exit 1
fi

# Check for flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${RED}Flask not found. Install with: pip install flask${NC}"
    exit 1
fi

# Determine which tests to run
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    api)
        echo -e "${YELLOW}Running API tests only...${NC}"
        pytest tests/test_api.py -v --tb=short
        ;;
    frontend)
        echo -e "${YELLOW}Running frontend tests only...${NC}"
        if ! python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
            echo -e "${RED}Playwright not found. Install with:${NC}"
            echo "  pip install pytest-playwright"
            echo "  playwright install chromium"
            exit 1
        fi
        pytest tests/test_frontend.py -v --tb=short
        ;;
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        echo

        echo -e "${GREEN}--- API Tests ---${NC}"
        pytest tests/test_api.py -v --tb=short
        echo

        if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
            echo -e "${GREEN}--- Frontend Tests ---${NC}"
            pytest tests/test_frontend.py -v --tb=short
        else
            echo -e "${YELLOW}Skipping frontend tests (Playwright not installed)${NC}"
            echo "  Install with: pip install pytest-playwright && playwright install chromium"
        fi
        ;;
    *)
        echo "Usage: $0 [api|frontend|all]"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Tests Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
