"""sk Harness — Spec-Driven Development plus state orchestration on top of spec-kit.

This package layers iteration-aware state management, DAG-driven task
dispatch, and observability primitives on top of the upstream ``spec-kit``
command catalog (see ``speckit/`` sibling package, preserved verbatim).

The public runtime surface lands in later tasks (T-04 onward); this
scaffold only declares versioning metadata so downstream modules can
import ``__version__`` and ``schema_version`` without a circular import.

References:
    * ERD §2 — Runtime & Language
    * ERD §15.1 — Schema versioning (``.skspec/.version``)
"""

__all__ = ["__version__", "schema_version"]

# Semantic version of the sk_harness package itself. Mirrors
# ``.skspec/.version`` and the PRD document version so a CLI run can
# refuse gracefully when state written by a newer binary is encountered
# (see ERD §15.2).
__version__: str = "0.3.0"

# State-file schema version. Separate symbol from ``__version__`` so a
# patch release of the binary that keeps the schema stable does not
# trigger spurious migration prompts.
schema_version: str = "0.3.0"
