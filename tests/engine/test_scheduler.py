"""Tests for DAGScheduler — ADR-018."""

# TODO(ADR-018): Test event-driven dispatch (blocks dispatched when ready).
# TODO(ADR-018): Test skip propagation (ERROR/CANCELLED → downstream SKIPPED).
# TODO(ADR-018): Test cancel propagation (cancel block → terminate + skip downstream).
# TODO(ADR-018): Test readiness check (all required inputs present).
# TODO(ADR-018): Test RunHandle wraps ProcessHandle and Future.
# TODO(ADR-018): Test skip_reasons dict populated correctly.
