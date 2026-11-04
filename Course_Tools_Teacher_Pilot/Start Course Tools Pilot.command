#!/bin/zsh
# Portable teacher pilot. No Git, cloud sync, or student account operations.
cd -- "$(dirname -- "$0")" || exit 1
clear
printf '\nCOURSE TOOLS TEACHER PILOT\n=========================\n\n'
if ! command -v python3 >/dev/null 2>&1; then
  printf 'Python 3 is needed on this Mac. The app could not start.\n'
  printf 'Ask your technology department to install Python 3, then double-click this file again.\n\n'
  read '?Press Return to close.'
  exit 1
fi
exec python3 server.py
