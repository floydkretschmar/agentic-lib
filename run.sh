#!/usr/bin/env sh
set -eu

run_test() {
  # JavaScript example:
  #   run package-manager test
  #   run package-manager typecheck
  python3 -m unittest discover --start-directory "$(git rev-parse --show-toplevel)/.codex/hooks" --pattern 'test_*.py'
  node --test "$(git rev-parse --show-toplevel)/.opencode/plugins/pre-tool-use/pre-tool-use.test.ts"
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
  python3 "$(git rev-parse --show-toplevel)/.codex/hooks/pre_tool_use_policy.py"
}

setup_environment() {
  if rtk hook codex --help >/dev/null 2>&1 && rtk hook opencode --help >/dev/null 2>&1; then
    echo "rtk already available"
  else
    echo "Install or upgrade rtk: https://www.rtk-ai.app/docs/getting-started/installation/" >&2
    exit 1
  fi

  if command -v context-mode >/dev/null 2>&1; then
    echo "context-mode already available"
  else
    npm install -g context-mode
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
