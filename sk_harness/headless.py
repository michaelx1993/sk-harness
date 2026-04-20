"""Headless runner entry point for overnight / CI execution.

Invoked via: `claude -p '/sk-go --until-pause --no-confirm' > sk.log`

The actual loop runs inside Claude Code; this module exists for:
1. Exit-code mapping (OQ-6 v0.2: five codes)
2. Pre-flight sanity checks before `/sk-go` delegates

Exit codes (per ERD §13 + OQ-6):
  0  clean completion (iteration done or user pause)
  1  generic error
  2  max_retries_exceeded
  3  deadlock
  4  prd_proposal pending and no-confirm rejected
"""

from __future__ import annotations

import sys

import click

from sk_harness.paths import Paths
from sk_harness.state.io import StateIO
from sk_harness.state.models import PauseReason


EXIT_CLEAN = 0
EXIT_ERROR = 1
EXIT_MAX_RETRIES = 2
EXIT_DEADLOCK = 3
EXIT_PRD_PROPOSAL = 4


def pause_reason_to_exit(reason: PauseReason | None) -> int:
    if reason is None:
        return EXIT_CLEAN
    return {
        PauseReason.user: EXIT_CLEAN,
        PauseReason.step: EXIT_CLEAN,
        PauseReason.max_retries_exceeded: EXIT_MAX_RETRIES,
        PauseReason.deadlock: EXIT_DEADLOCK,
        PauseReason.prd_proposal: EXIT_PRD_PROPOSAL,
    }.get(reason, EXIT_ERROR)


@click.command("headless-status")
def headless_status() -> None:
    """Print one-line status + exit with OQ-6 code. Use after /sk-go finishes."""
    try:
        paths = Paths.find()
        state = StateIO(paths).load_state()
    except Exception as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(EXIT_ERROR)
    code = pause_reason_to_exit(state.pause_reason) if state.paused else EXIT_CLEAN
    if state.phase.value == "completed":
        code = EXIT_CLEAN
    click.echo(
        f"phase={state.phase.value} paused={state.paused} "
        f"reason={state.pause_reason.value if state.pause_reason else 'none'} "
        f"exit={code}"
    )
    sys.exit(code)


if __name__ == "__main__":
    headless_status()
