#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then python -m venv .venv; fi
./.venv/bin/python -m pip install -e .
exec ./.venv/bin/python main.py "$@"
