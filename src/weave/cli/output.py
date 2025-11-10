"""Rich output formatters for Weave CLI."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from ..core.graph import DependencyGraph
from ..core.models import Agent, Weave, WeaveConfig


class WeaveOutput:
    """Formatted output utilities for Weave CLI."""

    def __init__(self, console: Console):
        self.console = console

    def print_plan(self, config: WeaveConfig, weave_name: str, graph: DependencyGraph) -> None:
        """
        Print execution plan in beautiful format.

        Args:
            config: Weave configuration
            weave_name: Name of weave to display
            graph: Dependency graph
        """
        weave = config.weaves[weave_name]
        execution_order = graph.get_execution_order()

        # Header
        self.console.print(f"\n📊 Execution Plan: [bold cyan]{weave_name}[/bold cyan]\n")

        if weave.description:
            self.console.print(f"[dim]{weave.description}[/dim]\n")

        # Agents table
        table = Table(title="Agents to Execute", show_header=True, header_style="bold magenta")
        table.add_column("Order", style="dim", width=6)
        table.add_column("Agent", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Tools", style="yellow")
        table.add_column("Inputs", style="blue")
        table.add_column("Outputs", style="magenta")

        for i, agent_name in enumerate(execution_order, 1):
            agent = graph.get_agent(agent_name)
            tools = ", ".join(agent.tools) if agent.tools else "-"
            inputs = agent.inputs or "-"
            outputs = agent.outputs or f"{agent_name}_output"

            table.add_row(
                str(i),
                agent_name,
                agent.model,
                tools,
                inputs,
                outputs,
            )

        self.console.print(table)
        self.console.print()

        # Execution flow
        self.console.print("[bold]Execution graph:[/bold]")
        flow = " → ".join(execution_order)
        self.console.print(f"  {flow}\n")

        # Summary
        self.console.print(
            f"[bold green]{len(execution_order)}[/bold green] agents will be executed.\n"
        )

    def print_agent_list(self, config: WeaveConfig) -> None:
        """Print list of all agents."""
        table = Table(title="Available Agents", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Tools", style="yellow")

        for name, agent in config.agents.items():
            tools = ", ".join(agent.tools) if agent.tools else "none"
            table.add_row(name, agent.model, tools)

        self.console.print(table)

    def print_weave_list(self, config: WeaveConfig) -> None:
        """Print list of all weaves."""
        table = Table(title="Available Weaves", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Agents", style="yellow")

        for name, weave in config.weaves.items():
            agents = ", ".join(weave.agents)
            desc = weave.description or "-"
            table.add_row(name, desc, agents)

        self.console.print(table)

    def print_error(self, error: Exception) -> None:
        """Print error in formatted panel."""
        self.console.print(
            Panel(
                f"[bold red]Error:[/bold red] {str(error)}",
                title="❌ Error",
                border_style="red",
            )
        )

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[bold green]✅ {message}[/bold green]")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")

    def print_graph_tree(self, graph: DependencyGraph) -> None:
        """Print dependency graph as a tree."""
        order = graph.get_execution_order()

        tree = Tree("🌳 Dependency Tree")

        for agent_name in order:
            agent = graph.get_agent(agent_name)
            node_label = f"[cyan]{agent_name}[/cyan] ([green]{agent.model}[/green])"

            if agent.inputs:
                # Find parent in tree
                tree.add(node_label)
            else:
                # Root node
                tree.add(node_label)

        self.console.print(tree)
