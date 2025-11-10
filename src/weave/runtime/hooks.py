"""Extension hooks for runtime execution."""

from typing import Any, Protocol, runtime_checkable

from ..core.models import Agent


@runtime_checkable
class ExecutorHook(Protocol):
    """
    Protocol for execution hooks.

    Hooks can intercept agent execution to add logging, metrics, notifications,
    or other custom behavior. Hooks can be synchronous or asynchronous.

    Example:
        class MyHook:
            async def before_agent(self, agent: Agent) -> None:
                print(f"Starting {agent.name}")

            async def after_agent(self, agent: Agent, output: Any) -> None:
                print(f"Completed {agent.name}")

        executor.register_hook(MyHook())
    """

    async def before_agent(self, agent: Agent) -> None:
        """
        Called before an agent starts execution.

        Args:
            agent: The agent about to execute
        """
        ...

    async def after_agent(self, agent: Agent, output: Any) -> None:
        """
        Called after an agent completes execution.

        Args:
            agent: The agent that executed
            output: The output from the agent (AgentOutput instance)
        """
        ...


class LoggingHook:
    """
    Example hook that logs execution to a file.

    Example:
        hook = LoggingHook("weave.log")
        executor.register_hook(hook)
    """

    def __init__(self, log_file: str):
        """
        Initialize logging hook.

        Args:
            log_file: Path to log file
        """
        self.log_file = log_file

    async def before_agent(self, agent: Agent) -> None:
        """Log agent start."""
        with open(self.log_file, "a") as f:
            f.write(f"[START] {agent.name} ({agent.model})\n")

    async def after_agent(self, agent: Agent, output: Any) -> None:
        """Log agent completion."""
        with open(self.log_file, "a") as f:
            if hasattr(output, "execution_time"):
                f.write(
                    f"[DONE] {agent.name} completed in {output.execution_time:.2f}s\n"
                )
            else:
                f.write(f"[DONE] {agent.name}\n")
