"""
Skills package - Dynamic skill loading and management.

This package provides the "Brain" layer for the Dynamic Skills architecture,
allowing business logic to be defined in Markdown files.
"""
from app.skills.registry import (
    SkillRegistry,
    SkillDef,
    get_skill_registry,
)

__all__ = [
    "SkillRegistry",
    "SkillDef",
    "get_skill_registry",
]
