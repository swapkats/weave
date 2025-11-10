"""Mock execution engine for Weave agents."""

import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rich.console import Console

from ..core.graph import DependencyGraph
from ..core.models import Agent
from .hooks import ExecutorHook


@dataclass
class AgentOutput:
    """Output from an agent execution."""

    agent_name: str
    output_key: str
    data: Any
    execution_time: float
    status: str  # "success" | "failed"
    tokens_used: int = 0


@dataclass
class ExecutionSummary:
    """Summary of a complete weave execution."""

    weave_name: str
    total_agents: int
    successful: int
    failed: int
    total_time: float
    outputs: Dict[str, AgentOutput]


class MockExecutor:
    """
    Mock agent execution engine for v1.

    Simulates agent execution with realistic delays and mock outputs.
    Designed with hooks for future real execution in v2.
    """

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        """
        Initialize executor.

        Args:
            console: Rich console for output (or create new one)
            verbose: Enable verbose output
        """
        self.console = console or Console()
        self.verbose = verbose
        self.outputs: Dict[str, AgentOutput] = {}
        self.hooks: List[ExecutorHook] = []

    def register_hook(self, hook: ExecutorHook) -> None:
        """Register an execution hook."""
        self.hooks.append(hook)

    def execute_agent(
        self, agent: Agent, inputs: Optional[AgentOutput] = None
    ) -> AgentOutput:
        """
        Execute a single agent (mocked).

        Args:
            agent: Agent to execute
            inputs: Optional output from upstream agent

        Returns:
            AgentOutput with mock results
        """
        # Call before hooks
        for hook in self.hooks:
            hook.before_agent(agent)

        start_time = time.time()

        # Show tools
        if agent.tools:
            tools_str = ", ".join(agent.tools)
            self.console.print(f"  ⚙️  Running with tools: {tools_str}")
        else:
            self.console.print("  ⚙️  Running (no tools)")

        # Simulate processing time (0.5-2.5 seconds)
        delay = random.uniform(0.5, 2.5)
        if self.verbose:
            self.console.print(f"  ⏳ Simulating work for {delay:.1f}s...")

        time.sleep(delay)

        execution_time = time.time() - start_time

        # Generate mock output
        output_key = agent.outputs or f"{agent.name}_output"
        tokens = random.randint(100, 1500)

        mock_data = {
            "model": agent.model,
            "input_from": inputs.agent_name if inputs else None,
            "result": f"[Mock output from {agent.name} using {agent.model}]",
            "tokens": tokens,
            "config": agent.config,
        }

        result = AgentOutput(
            agent_name=agent.name,
            output_key=output_key,
            data=mock_data,
            execution_time=execution_time,
            status="success",
            tokens_used=tokens,
        )

        # Store output for downstream agents
        self.outputs[agent.name] = result

        self.console.print(f"  ⏱️  Execution time: {execution_time:.1f}s")
        self.console.print(f"  ✅ Output: {output_key} ({tokens} tokens)")

        # Call after hooks
        for hook in self.hooks:
            hook.after_agent(agent, result)

        return result

    def execute_flow(
        self, graph: DependencyGraph, weave_name: str, dry_run: bool = False
    ) -> ExecutionSummary:
        """
        Execute entire agent flow.

        Args:
            graph: Dependency graph to execute
            weave_name: Name of weave being executed
            dry_run: If True, only show what would be executed

        Returns:
            ExecutionSummary with results
        """
        execution_order = graph.get_execution_order()
        total_agents = len(execution_order)

        self.console.print(f"\n🚀 {'[DRY RUN] ' if dry_run else ''}Applying weave: {weave_name}\n")
        self.console.print("Executing agents in order:")
        self.console.print("━" * 50 + "\n")

        start_time = time.time()
        successful = 0
        failed = 0

        for i, agent_name in enumerate(execution_order, 1):
            agent = graph.get_agent(agent_name)

            self.console.print(f"[{i}/{total_agents}] {agent_name} ({agent.model})")

            if dry_run:
                self.console.print("  [DRY RUN] Would execute this agent")
                if agent.inputs:
                    self.console.print(f"  [DRY RUN] Would use input from: {agent.inputs}")
                self.console.print()
                continue

            # Get input from upstream agent
            upstream_output = None
            if agent.inputs:
                upstream_output = self.outputs.get(agent.inputs)
                if upstream_output:
                    self.console.print(f"  📥 Input from: {agent.inputs}")

            # Execute
            try:
                result = self.execute_agent(agent, upstream_output)
                successful += 1
            except Exception as e:
                self.console.print(f"  ❌ Execution failed: {e}")
                failed += 1

            self.console.print()  # Blank line between agents

        total_time = time.time() - start_time

        self.console.print("━" * 50 + "\n")

        if not dry_run:
            # Print summary
            status = "SUCCESS" if failed == 0 else "PARTIAL" if successful > 0 else "FAILED"
            status_emoji = "✨" if failed == 0 else "⚠️" if successful > 0 else "❌"

            self.console.print(f"{status_emoji} {'Dry run' if dry_run else 'Apply'} complete!\n")
            self.console.print("Summary:")
            self.console.print(f"  Agents executed: {successful}/{total_agents}")
            if failed > 0:
                self.console.print(f"  Failed: {failed}")
            self.console.print(f"  Total time: {total_time:.1f}s")
            self.console.print(f"  Status: {status}")

            # Show final output
            if execution_order and execution_order[-1] in self.outputs:
                final = self.outputs[execution_order[-1]]
                self.console.print(f"\nFinal output: {final.output_key}")

        return ExecutionSummary(
            weave_name=weave_name,
            total_agents=total_agents,
            successful=successful,
            failed=failed,
            total_time=total_time,
            outputs=self.outputs.copy(),
        )
