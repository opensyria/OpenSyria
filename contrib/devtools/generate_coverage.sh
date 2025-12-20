#!/bin/bash
# generate_coverage.sh - Generate code coverage report locally
# Usage: ./contrib/devtools/generate_coverage.sh [test_filter]
#
# Examples:
#   ./contrib/devtools/generate_coverage.sh              # All tests
#   ./contrib/devtools/generate_coverage.sh randomx_*    # RandomX tests only
#   ./contrib/devtools/generate_coverage.sh pow_tests    # PoW tests only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build_coverage"
REPORT_DIR="${ROOT_DIR}/coverage_report"

# Test filter (default: all randomx + pow tests)
TEST_FILTER="${1:-randomx_*,pow_tests}"

echo "============================================"
echo "OpenSY Code Coverage Generator"
echo "============================================"
echo "Root dir: ${ROOT_DIR}"
echo "Build dir: ${BUILD_DIR}"
echo "Test filter: ${TEST_FILTER}"
echo ""

# Check for lcov
if ! command -v lcov &> /dev/null; then
    echo "ERROR: lcov not found. Install with:"
    echo "  macOS: brew install lcov"
    echo "  Ubuntu: sudo apt install lcov"
    exit 1
fi

# Clean build directory
echo "[1/5] Preparing coverage build..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Configure with coverage flags
echo "[2/5] Configuring with coverage flags..."
cmake "${ROOT_DIR}" \
    -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_FLAGS="--coverage -fprofile-arcs -ftest-coverage -O0" \
    -DCMAKE_CXX_FLAGS="--coverage -fprofile-arcs -ftest-coverage -O0" \
    -DCMAKE_EXE_LINKER_FLAGS="--coverage" \
    -DBUILD_TESTS=ON

# Build
echo "[3/5] Building (this may take a few minutes)..."
cmake --build . -j$(sysctl -n hw.ncpu 2>/dev/null || nproc)

# Run tests
echo "[4/5] Running tests: ${TEST_FILTER}"
# Split comma-separated filters
IFS=',' read -ra FILTERS <<< "${TEST_FILTER}"
for filter in "${FILTERS[@]}"; do
    echo "  Running: ${filter}"
    ./bin/test_opensy --run_test="${filter}" --log_level=warning || true
done

# Generate coverage report
echo "[5/5] Generating coverage report..."
rm -rf "${REPORT_DIR}"
mkdir -p "${REPORT_DIR}"

# Capture coverage
lcov --capture \
    --directory . \
    --output-file coverage.info \
    --ignore-errors mismatch 2>/dev/null || true

# Filter out system/test code
lcov --remove coverage.info \
    '/usr/*' \
    '/Library/*' \
    '/opt/*' \
    '*/test/*' \
    '*/build*/_deps/*' \
    '*/randomx-src/*' \
    --output-file coverage.filtered.info \
    --ignore-errors unused 2>/dev/null || true

# Generate HTML report
genhtml coverage.filtered.info \
    --output-directory "${REPORT_DIR}" \
    --title "OpenSY Coverage Report" \
    --legend \
    --show-details 2>/dev/null || true

# Summary
echo ""
echo "============================================"
echo "Coverage Report Generated!"
echo "============================================"
echo ""

if [ -f coverage.filtered.info ]; then
    lcov --summary coverage.filtered.info 2>&1 | grep -E "lines|functions|branches" || true
fi

echo ""
echo "HTML report: ${REPORT_DIR}/index.html"
echo ""

# Try to open in browser (macOS)
if command -v open &> /dev/null; then
    read -p "Open report in browser? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "${REPORT_DIR}/index.html"
    fi
fi
