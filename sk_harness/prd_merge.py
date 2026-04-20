"""Backward-compat shim. Use `sk_harness.proposals` directly in new code."""

from sk_harness.proposals import (
    accept_proposal,
    file_proposal,
    list_pending,
    reject_proposal,
)

__all__ = ["accept_proposal", "file_proposal", "list_pending", "reject_proposal"]
