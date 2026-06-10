# agent.py  — top-level ADK entrypoint for Agent Engine deployment.
# Agent Engine stages this file alongside the `app/` package so that
# `from app.agent import root_agent` can be resolved correctly.

from app.agent import root_agent  # noqa: F401

__all__ = ["root_agent"]
