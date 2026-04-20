#!/usr/bin/env bash
# Install sk-harness: Python CLI + Claude Code skills
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_ROOT/.claude/skills"
SKILLS_DEST="${SK_SKILLS_DEST:-$HOME/.claude/skills}"

echo "→ Installing sk-harness as a global tool (so /sk-* skills can invoke 'sk' on PATH)"
cd "$REPO_ROOT"
if command -v uv >/dev/null 2>&1; then
    uv tool install . --force
    echo "  Installed via 'uv tool install'; 'sk' is now on PATH at ~/.local/bin/sk"
elif command -v pipx >/dev/null 2>&1; then
    pipx install --force .
    echo "  Installed via pipx; 'sk' is now on PATH"
else
    echo "  !! Need either 'uv' (recommended) or 'pipx' to install globally."
    echo "  !! Install uv: https://github.com/astral-sh/uv"
    echo "  !! Then rerun this script."
    exit 1
fi

if ! command -v sk >/dev/null 2>&1; then
    echo "  !! 'sk' not found on PATH after install."
    echo "  !! Ensure ~/.local/bin is in your PATH:"
    echo "     export PATH=\"\$HOME/.local/bin:\$PATH\"    # add to ~/.zshrc or ~/.bashrc"
    exit 1
fi
echo "  sk version: $(sk --version)"

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
