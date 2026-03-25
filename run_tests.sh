#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

echo "=========================================================="
echo " Acceptance Test Runner"
echo "=========================================================="
echo "[INFO] Root: $ROOT_DIR"
echo "[INFO] Unit tests: $ROOT_DIR/unit_tests"
echo "[INFO] API tests: $ROOT_DIR/API_tests"
echo

TOTAL=0
PASSED=0
FAILED=0
FAILED_GROUPS=()

run_group() {
  local name="$1"
  local cmd="$2"
  TOTAL=$((TOTAL + 1))
  echo "----------------------------------------------------------"
  echo "[RUN] $name"
  echo "----------------------------------------------------------"
  set +e
  eval "$cmd"
  local rc=$?
  set -e
  if [ $rc -eq 0 ]; then
    PASSED=$((PASSED + 1))
    echo "[PASS] $name"
  else
    FAILED=$((FAILED + 1))
    FAILED_GROUPS+=("$name")
    echo "[FAIL] $name (exit code $rc)"
  fi
  echo
}

if [ ! -d "$ROOT_DIR/unit_tests" ]; then
  echo "[FAIL] unit_tests directory missing"
  exit 1
fi

if [ ! -d "$ROOT_DIR/API_tests" ]; then
  echo "[FAIL] API_tests directory missing"
  exit 1
fi

run_group "Unit tests" "docker compose run --rm backend sh -c 'cd /workspace && PYTHONPATH=/workspace/backend pytest -q unit_tests'"

run_group "API functional tests" "python3 $ROOT_DIR/API_tests/test_api_functional.py"

echo "=========================================================="
echo " Test Summary"
echo "=========================================================="
echo "total_groups=$TOTAL"
echo "passed_groups=$PASSED"
echo "failed_groups=$FAILED"

if [ $FAILED -gt 0 ]; then
  echo "failed_list=${FAILED_GROUPS[*]}"
  exit 1
fi

echo "All test groups passed."
