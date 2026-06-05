#!/usr/bin/env sh
set -eu

run_test() {
  # JavaScript example:
  #   run package-manager test
  #   run package-manager typecheck
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

case "${1:-}" in
  test)
    run_test
    ;;
  format)
    run_format
    ;;
  build)
    run_build
    ;;
  *)
    echo "Usage: $0 {test|format|build}" >&2
    exit 2
    ;;
esac
