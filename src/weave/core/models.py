"""Pydantic models for Weave configuration."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class AgentConfig(BaseModel):
    """Configuration for an agent's behavior."""

    model_config = ConfigDict(extra="allow")  # Allow custom fields

    temperature: float = 0.7
    max_tokens: int = 1000


class Agent(BaseModel):
    """An AI agent definition."""

    name: str = ""  # Will be injected from dict key
    model: str
    tools: List[str] = Field(default_factory=list)
    inputs: Optional[str] = None  # Reference to another agent
    outputs: Optional[str] = None  # Output key name
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("inputs")
    @classmethod
    def normalize_inputs(cls, v: Optional[str]) -> Optional[str]:
        """Normalize inputs to just agent name (strip .outputs if present)."""
        if v and "." in v:
            return v.split(".")[0]  # "researcher.outputs" -> "researcher"
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure agent name is valid identifier."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Agent name must be alphanumeric with - or _: {v}")
        return v


class Weave(BaseModel):
    """An orchestration flow definition."""

    name: str = ""  # Will be injected from dict key
    description: str = ""
    agents: List[str]

    @field_validator("agents")
    @classmethod
    def validate_agents_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure weave has at least one agent."""
        if not v:
            raise ValueError("Weave must contain at least one agent")
        return v


class WeaveConfig(BaseModel):
    """Complete Weave configuration file."""

    version: str = "1.0"
    env: Dict[str, str] = Field(default_factory=dict)
    agents: Dict[str, Agent]
    weaves: Dict[str, Weave]

    @model_validator(mode="after")
    def validate_references(self) -> "WeaveConfig":
        """Validate all agent references are valid."""
        agent_names = set(self.agents.keys())

        # Inject agent names into agent objects
        for name, agent in self.agents.items():
            agent.name = name

        # Check inputs reference valid agents
        for name, agent in self.agents.items():
            if agent.inputs and agent.inputs not in agent_names:
                raise ValueError(
                    f"Agent '{name}' references unknown input agent '{agent.inputs}'"
                )

        # Check weaves reference valid agents
        for weave_name, weave in self.weaves.items():
            weave.name = weave_name
            for agent_name in weave.agents:
                if agent_name not in agent_names:
                    raise ValueError(
                        f"Weave '{weave_name}' references unknown agent '{agent_name}'"
                    )

        return self

    @model_validator(mode="after")
    def ensure_at_least_one_weave(self) -> "WeaveConfig":
        """Ensure at least one weave is defined."""
        if not self.weaves:
            raise ValueError("Configuration must define at least one weave")
        return self
