#!/usr/bin/env bash
# Install sk-harness: Python CLI + Claude Code skills
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_ROOT/.claude/skills"
SKILLS_DEST="${SK_SKILLS_DEST:-$HOME/.claude/skills}"

echo "→ Installing sk-harness Python package (editable)"
cd "$REPO_ROOT"
if command -v uv >/dev/null 2>&1; then
    uv sync
    echo "  Installed via uv; run with: uv run sk --help"
    echo "  Or activate venv: source .venv/bin/activate && sk --help"
else
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -e .
    echo "  Installed via pip (venv); activate with: source .venv/bin/activate"
fi

echo
echo "→ Registering Claude Code skills into $SKILLS_DEST"
mkdir -p "$SKILLS_DEST"
for dir in "$SKILLS_SRC"/sk-*/; do
    name="$(basename "$dir")"
    dest="$SKILLS_DEST/$name"
    if [ -L "$dest" ] || [ -d "$dest" ]; then
        echo "  · $name exists; skipping (remove manually if you want to overwrite)"
        continue
    fi
    ln -s "$dir" "$dest"
    echo "  ✓ $name"
done

echo
echo "Done. Next:"
echo "  cd your-project/"
echo "  claude                   # start Claude Code"
echo "  /sk-init                 # bootstrap .skspec/"
echo "  /sk-constitution         # ratify project principles"
echo "  /sk-specify              # draft your first PRD"
echo "  /sk-go                   # hand off to TPM loop"
