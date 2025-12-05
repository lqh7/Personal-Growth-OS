"""
SkillRegistry - Dynamic skill loading from Markdown files.

This module implements the "Brain" layer of the Brain-Hand separation architecture,
loading business logic (SOP) from Markdown files with YAML frontmatter.

Key Features:
- Hot-reloadable skill definitions (no restart needed)
- YAML frontmatter for metadata (tools, description, settings)
- Markdown body as SOP (Standard Operating Procedure)
- Skill caching with invalidation support
"""
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillDef:
    """
    Parsed skill definition from Markdown file.

    Attributes:
        name: Skill identifier (filename without .md)
        description: Short description for orchestrator routing
        tools: List of tool names this skill can use
        sop: The SOP content (Markdown body)
        inherit_history: Whether to include conversation history
        max_iterations: Maximum tool call iterations (prevents infinite loops)
    """
    name: str
    description: str
    tools: List[str]
    sop: str
    inherit_history: bool = True
    max_iterations: int = 10


class SkillRegistry:
    """
    Registry for loading and managing skill definitions from Markdown files.

    Skills are defined in .md files with YAML frontmatter:

    ```markdown
    ---
    name: task_manager
    description: Task management - create, update, delete, snooze tasks
    tools:
      - task_get
      - task_list
      - task_create
    inherit_history: true
    ---

    ## Role
    You are a task management expert...

    ## SOP
    ### Creating a Task
    1. Confirm task title...
    ```

    Usage:
        registry = SkillRegistry()
        skill = registry.load_skill("task_manager")
        print(skill.sop)  # Get the SOP content
        print(skill.tools)  # ['task_get', 'task_list', 'task_create']
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize the skill registry.

        Args:
            skills_dir: Directory containing .md skill files.
                       Defaults to the same directory as this module.
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent
        self.skills_dir = skills_dir
        self._cache: Dict[str, SkillDef] = {}
        self._file_mtimes: Dict[str, float] = {}  # For cache invalidation

    def load_skill(self, skill_name: str, force_reload: bool = False) -> SkillDef:
        """
        Load a skill definition from Markdown file.

        Args:
            skill_name: Name of the skill (filename without .md extension)
            force_reload: If True, bypass cache and reload from disk

        Returns:
            SkillDef with parsed metadata and SOP

        Raises:
            FileNotFoundError: If skill file doesn't exist
            ValueError: If skill file format is invalid
        """
        md_path = self.skills_dir / f"{skill_name}.md"

        if not md_path.exists():
            raise FileNotFoundError(
                f"Skill '{skill_name}' not found at {md_path}. "
                f"Available skills: {self.list_skills()}"
            )

        # Check cache validity
        current_mtime = md_path.stat().st_mtime
        if not force_reload and skill_name in self._cache:
            if self._file_mtimes.get(skill_name) == current_mtime:
                logger.debug(f"Using cached skill: {skill_name}")
                return self._cache[skill_name]

        # Parse the Markdown file
        logger.info(f"Loading skill from: {md_path}")
        content = md_path.read_text(encoding="utf-8")
        skill = self._parse_skill_file(skill_name, content)

        # Update cache
        self._cache[skill_name] = skill
        self._file_mtimes[skill_name] = current_mtime

        return skill

    def _parse_skill_file(self, skill_name: str, content: str) -> SkillDef:
        """
        Parse a skill Markdown file with YAML frontmatter.

        Expected format:
        ---
        name: skill_name
        description: Skill description
        tools:
          - tool1
          - tool2
        inherit_history: true
        ---

        # SOP Content here...
        """
        if not content.startswith("---"):
            raise ValueError(
                f"Skill file must start with YAML frontmatter (---). "
                f"See doc/动态技能架构设计.md for format."
            )

        # Split frontmatter and body
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(
                f"Invalid skill file format. Expected: ---\\nYAML\\n---\\nMarkdown"
            )

        yaml_content = parts[1].strip()
        sop_content = parts[2].strip()

        # Parse YAML
        try:
            metadata = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in frontmatter: {e}")

        if not isinstance(metadata, dict):
            raise ValueError("YAML frontmatter must be a dictionary")

        # Validate required fields
        if "tools" not in metadata:
            raise ValueError("Skill must define 'tools' list in frontmatter")

        # Build SkillDef
        return SkillDef(
            name=metadata.get("name", skill_name),
            description=metadata.get("description", ""),
            tools=metadata.get("tools", []),
            sop=sop_content,
            inherit_history=metadata.get("inherit_history", True),
            max_iterations=metadata.get("max_iterations", 10),
        )

    def list_skills(self) -> List[str]:
        """
        List all available skill names.

        Returns:
            List of skill names (filenames without .md)
        """
        return [
            p.stem for p in self.skills_dir.glob("*.md")
            if not p.name.startswith("_")  # Skip files starting with underscore
        ]

    def get_all_skill_descriptions(self) -> List[Dict[str, str]]:
        """
        Get descriptions of all available skills.

        Used by the orchestrator to decide which skill to activate.

        Returns:
            List of dicts with 'name' and 'description' keys
        """
        descriptions = []
        for skill_name in self.list_skills():
            try:
                skill = self.load_skill(skill_name)
                descriptions.append({
                    "name": skill.name,
                    "description": skill.description
                })
            except Exception as e:
                logger.warning(f"Failed to load skill {skill_name}: {e}")
                continue
        return descriptions

    def clear_cache(self):
        """Clear the skill cache (force reload on next access)."""
        self._cache.clear()
        self._file_mtimes.clear()
        logger.info("Skill cache cleared")

    def get_skill_sop_for_injection(self, skill_name: str) -> str:
        """
        Get formatted SOP for suffix injection into conversation.

        This method formats the SOP with clear boundaries for the LLM.

        Args:
            skill_name: Name of the skill

        Returns:
            Formatted SOP string ready for injection

        Example output:
            <skill name="task_manager">
            ## Role
            You are a task management expert...
            </skill>
        """
        skill = self.load_skill(skill_name)
        return f"""<skill name="{skill.name}">
{skill.sop}
</skill>

Available tools for this skill: {", ".join(skill.tools)}

IMPORTANT: Follow the SOP above. When done, send appropriate UI commands to refresh data.
"""


# ============================================
# Singleton Instance
# ============================================

_registry_instance: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """
    Get the global skill registry instance.

    Returns:
        SkillRegistry singleton
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SkillRegistry()
    return _registry_instance
