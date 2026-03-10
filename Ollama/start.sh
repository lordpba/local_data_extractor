#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run setup if venv is missing
if [[ ! -d ".venv" ]]; then
  ./setup.sh
fi

# Activate venv and ensure deps
source .venv/bin/activate
pip install -r requirements.txt

# Start the app
python app.py
