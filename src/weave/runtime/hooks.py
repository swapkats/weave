"""Extension hooks for runtime execution."""

from typing import Any, Protocol

from ..core.models import Agent


class ExecutorHook(Protocol):
    """Protocol for execution hooks (extension point for v2)."""

    def before_agent(self, agent: Agent) -> None:
        """
        Called before an agent starts execution.

        Args:
            agent: The agent about to execute
        """
        ...

    def after_agent(self, agent: Agent, output: Any) -> None:
        """
        Called after an agent completes execution.

        Args:
            agent: The agent that executed
            output: The output from the agent
        """
        ...


class LoggingHook:
    """Example hook that logs execution to a file."""

    def __init__(self, log_file: str):
        self.log_file = log_file

    def before_agent(self, agent: Agent) -> None:
        """Log agent start."""
        with open(self.log_file, "a") as f:
            f.write(f"[START] {agent.name} ({agent.model})\n")

    def after_agent(self, agent: Agent, output: Any) -> None:
        """Log agent completion."""
        with open(self.log_file, "a") as f:
            if hasattr(output, "execution_time"):
                f.write(
                    f"[DONE] {agent.name} completed in {output.execution_time:.2f}s\n"
                )
            else:
                f.write(f"[DONE] {agent.name}\n")
