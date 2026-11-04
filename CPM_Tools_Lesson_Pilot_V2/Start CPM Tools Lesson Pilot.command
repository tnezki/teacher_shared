#!/bin/zsh
# Local-only CPM Tools Lesson Builder pilot. No Git operations.
set -e
HERE="${0:A:h}"
cd "$HERE"
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo 'Python 3 is required to run the local teacher pilot.'
  echo 'Press Enter to close.'
  read -r
  exit 1
fi
exec "$PYTHON_BIN" -u "$HERE/server.py"
