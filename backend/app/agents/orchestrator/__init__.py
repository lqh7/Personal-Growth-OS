"""
Orchestrator Agent - Dynamic skill-based agent system.

This package implements the LangGraph orchestrator that:
1. Routes user requests to appropriate skills
2. Loads skill SOP via suffix injection
3. Executes specialist agent with skill-specific tools
4. Handles multi-round continuation
"""
from app.agents.orchestrator.graph import (
    create_orchestrator_graph,
    get_orchestrator,
)
from app.agents.orchestrator.state import OrchestratorState

__all__ = [
    "create_orchestrator_graph",
    "get_orchestrator",
    "OrchestratorState",
]
