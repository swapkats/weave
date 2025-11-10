"""Dependency graph builder and analyzer."""

from typing import Dict, List

import networkx as nx

from .exceptions import GraphError
from .models import Agent, Weave, WeaveConfig


class DependencyGraph:
    """Build and analyze agent dependency graphs."""

    def __init__(self, config: WeaveConfig):
        """
        Initialize graph builder.

        Args:
            config: Validated Weave configuration
        """
        self.config = config
        self.graph = nx.DiGraph()

    def build(self, weave_name: str) -> "DependencyGraph":
        """
        Build dependency graph for a specific weave.

        Args:
            weave_name: Name of the weave to build graph for

        Returns:
            Self for method chaining

        Raises:
            GraphError: If weave not found
        """
        if weave_name not in self.config.weaves:
            available = ", ".join(self.config.weaves.keys())
            raise GraphError(
                f"Weave '{weave_name}' not found. Available weaves: {available}"
            )

        weave = self.config.weaves[weave_name]
        agents = {name: self.config.agents[name] for name in weave.agents}

        # Add nodes
        for name, agent in agents.items():
            self.graph.add_node(name, agent=agent)

        # Add edges based on inputs
        for name, agent in agents.items():
            if agent.inputs:
                # Edge from input agent to this agent
                if agent.inputs in agents:
                    self.graph.add_edge(agent.inputs, name)
                else:
                    # Input agent not in this weave
                    raise GraphError(
                        f"Agent '{name}' depends on '{agent.inputs}' "
                        f"which is not part of weave '{weave_name}'"
                    )

        return self

    def validate(self) -> None:
        """
        Validate graph structure.

        Raises:
            GraphError: If graph contains cycles or other structural issues
        """
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            cycle_str = " -> ".join(cycles[0]) + f" -> {cycles[0][0]}"
            raise GraphError(
                f"Circular dependency detected: {cycle_str}\n"
                f"Agents cannot have circular input dependencies."
            )

        # Check for empty graph
        if len(self.graph.nodes) == 0:
            raise GraphError("Graph is empty - no agents to execute")

    def get_execution_order(self) -> List[str]:
        """
        Get topologically sorted execution order.

        Returns:
            List of agent names in execution order

        Raises:
            GraphError: If unable to determine order
        """
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError as e:
            raise GraphError(f"Cannot determine execution order: {e}")

    def get_agent(self, name: str) -> Agent:
        """Get agent from graph."""
        return self.graph.nodes[name]["agent"]

    def get_dependencies(self, agent_name: str) -> List[str]:
        """
        Get all upstream dependencies for an agent.

        Args:
            agent_name: Name of agent

        Returns:
            List of agent names this agent depends on
        """
        return list(nx.ancestors(self.graph, agent_name))

    def get_dependents(self, agent_name: str) -> List[str]:
        """
        Get all downstream dependents of an agent.

        Args:
            agent_name: Name of agent

        Returns:
            List of agent names that depend on this agent
        """
        return list(nx.descendants(self.graph, agent_name))

    def to_ascii(self) -> str:
        """
        Generate ASCII art representation of the graph.

        Returns:
            ASCII diagram as string
        """
        order = self.get_execution_order()

        if not order:
            return "(empty graph)"

        lines = []
        for i, agent_name in enumerate(order):
            agent = self.get_agent(agent_name)

            # Calculate box width based on content
            name_len = len(agent_name)
            model_len = len(agent.model)
            width = max(name_len, model_len) + 4

            # Draw box
            top = "       ┌" + "─" * width + "┐"
            name_line = f"       │ {agent_name:^{width-2}} │"
            model_line = f"       │ {agent.model:^{width-2}} │"
            bottom = "       └" + "─" * (width - 2) + "┬" + "─" + "┘"

            lines.append(top)
            lines.append(name_line)
            lines.append(model_line)
            lines.append(bottom)

            # Arrow to next (if not last)
            if i < len(order) - 1:
                lines.append("              │")
                lines.append("              ▼")

        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """
        Generate Mermaid diagram syntax.

        Returns:
            Mermaid diagram as string
        """
        lines = ["graph TD"]

        # Add nodes
        for name in self.graph.nodes():
            agent = self.get_agent(name)
            # Escape special characters in labels
            safe_name = name.replace("-", "_")
            lines.append(f"    {safe_name}[\"{agent.name}<br/>{agent.model}\"]")

        # Add edges
        for source, target in self.graph.edges():
            safe_source = source.replace("-", "_")
            safe_target = target.replace("-", "_")
            lines.append(f"    {safe_source} --> {safe_target}")

        # If no edges, note it
        if len(self.graph.edges()) == 0 and len(self.graph.nodes()) > 0:
            lines.append("    %% No dependencies - agents will run independently")

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, any]:
        """
        Get summary statistics about the graph.

        Returns:
            Dictionary with graph statistics
        """
        order = self.get_execution_order()
        return {
            "total_agents": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "execution_order": order,
            "has_parallel": len(self.graph.edges) < len(self.graph.nodes) - 1,
        }
