#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run setup if venv is missing
if [[ ! -d ".venv" ]]; then
  echo "Virtual environment not found. Running setup..."
  ./setup.sh
fi

# 1. Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
pip install -q -r requirements.txt

# 3. Open browser at: http://localhost:5000
echo "Opening browser at http://localhost:5000..."
(sleep 2 && xdg-open http://localhost:5000 2>/dev/null || open http://localhost:5000 2>/dev/null) &

# 2. Run the app
echo "Starting application..."
python3 src/app.py
