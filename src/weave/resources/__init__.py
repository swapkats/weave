"""Resource loading system for Weave.

Loads prompts, skills, recipes, knowledge bases, rules, and configurations
from files and folders.
"""

from .loader import ResourceLoader, ResourceType
from .models import (
    SystemPrompt,
    Skill,
    Recipe,
    KnowledgeBase,
    Rule,
    AgentBehavior,
)

__all__ = [
    "ResourceLoader",
    "ResourceType",
    "SystemPrompt",
    "Skill",
    "Recipe",
    "KnowledgeBase",
    "Rule",
    "AgentBehavior",
]
