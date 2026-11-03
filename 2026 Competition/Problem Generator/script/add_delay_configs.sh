#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"
generator="$script_dir/delay_generator.py"

targets=(
  "$repo_root/Example Instances"
  "$repo_root/Main Round Evaluation Instances"
  "$repo_root/Test Round Evaluation Instances"
)

usage() {
  cat <<'EOF'
Usage: add_delay_configs.sh [delay_generator.py options]

Runs delay_generator.py for:
  - Example Instances
  - Main Round Evaluation Instances
  - Test Round Evaluation Instances

Examples:
  ./add_delay_configs.sh
  ./add_delay_configs.sh --seed 7 --agentCounter 20
  ./add_delay_configs.sh --overwrite --eventModel poisson

Environment:
  PYTHON_BIN   Python executable to use (default: python3)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -f "$generator" ]]; then
  echo "Missing generator: $generator" >&2
  exit 1
fi

for target in "${targets[@]}"; do
  if [[ ! -d "$target" ]]; then
    echo "Skipping missing directory: $target" >&2
    continue
  fi

  echo "Adding delayConfig in: $target"
  "$python_bin" "$generator" --proposalDir "$target" "$@"
done
