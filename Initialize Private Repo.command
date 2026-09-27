#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo
if [ -d .git ]; then
  echo "This folder is already a Git repository:"
  echo "$ROOT"
else
  git init -b main
  echo "Initialized local Git repository:"
  echo "$ROOT"
fi

echo
echo "Next: open GitHub Desktop -> File -> Add Local Repository, select this folder,"
echo "then Publish repository and keep it PRIVATE."
echo
read -p "Press Return to close..."
