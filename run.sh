#!/usr/bin/env sh
set -eu

run_test() {
  # JavaScript example:
  #   run package-manager test
  #   run package-manager typecheck
  python3 -m unittest discover --start-directory "$(git rev-parse --show-toplevel)/hooks" --pattern 'test_*.py'
}

run_lint() {
  # JavaScript example:
  #   run package-manager lint
  :
}

run_format() {
  # JavaScript example:
  #   run prettier across the repository
  :
}

run_build() {
  # JavaScript example:
  #   run package-manager build
  :
}

safety_hook() {
  project_directory="$(git rev-parse --show-toplevel)"
  python3 "$project_directory/hooks/pre_tool_use_policy.py" "$project_directory"
}

setup_environment() {
  if command -v rtk >/dev/null 2>&1; then
    echo "rtk already available"
  else
    echo "Install rtk: https://www.rtk-ai.app/docs/getting-started/installation/" >&2
    exit 1
  fi
}

case "${1:-}" in
  test)
    run_test
    ;;
  lint)
    run_lint
    ;;
  format)
    run_format
    ;;
  build)
    run_build
    ;;
  safety-hook)
    safety_hook
    ;;
  setup-environment)
    setup_environment
    ;;
  *)
    echo "Usage: $0 {test|lint|format|build|safety-hook|setup-environment}" >&2
    exit 2
    ;;
esac
