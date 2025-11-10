"""Tests for executor hooks functionality."""

import pytest
import asyncio
from pathlib import Path
from typing import Any, List
from dataclasses import dataclass, field

from weave.runtime.executor import Executor, AgentOutput
from weave.runtime.hooks import ExecutorHook, LoggingHook
from weave.core.models import Agent, WeaveConfig, Weave
from weave.core.graph import DependencyGraph


@dataclass
class MockHook:
    """Mock hook for testing."""

    before_calls: List[str] = field(default_factory=list)
    after_calls: List[str] = field(default_factory=list)
    should_fail: bool = False

    async def before_agent(self, agent: Agent) -> None:
        """Record before_agent call."""
        if self.should_fail:
            raise RuntimeError(f"Mock failure in before_agent for {agent.name}")
        self.before_calls.append(agent.name)

    async def after_agent(self, agent: Agent, output: Any) -> None:
        """Record after_agent call."""
        if self.should_fail:
            raise RuntimeError(f"Mock failure in after_agent for {agent.name}")
        self.after_calls.append(agent.name)


@dataclass
class MetricsHook:
    """Hook that collects execution metrics."""

    metrics: dict = field(default_factory=dict)

    async def before_agent(self, agent: Agent) -> None:
        """Record agent start."""
        import time

        self.metrics[agent.name] = {
            "start_time": time.time(),
            "model": agent.model,
        }

    async def after_agent(self, agent: Agent, output: Any) -> None:
        """Record agent completion."""
        import time

        metrics = self.metrics[agent.name]
        metrics["end_time"] = time.time()
        metrics["duration"] = metrics["end_time"] - metrics["start_time"]
        metrics["status"] = output.status if hasattr(output, "status") else "unknown"
        metrics["tokens"] = (
            output.tokens_used if hasattr(output, "tokens_used") else 0
        )


class TestExecutorHook:
    """Test ExecutorHook protocol."""

    def test_mock_hook_implements_protocol(self):
        """MockHook should implement ExecutorHook protocol."""
        hook = MockHook()
        assert isinstance(hook, ExecutorHook)

    def test_logging_hook_implements_protocol(self):
        """LoggingHook should implement ExecutorHook protocol."""
        hook = LoggingHook("test.log")
        assert isinstance(hook, ExecutorHook)

    def test_metrics_hook_implements_protocol(self):
        """MetricsHook should implement ExecutorHook protocol."""
        hook = MetricsHook()
        assert isinstance(hook, ExecutorHook)


class TestExecutorRegisterHook:
    """Test Executor.register_hook() method."""

    def test_register_hook(self):
        """Should register a hook successfully."""
        executor = Executor()
        hook = MockHook()

        executor.register_hook(hook)

        assert len(executor.hooks) == 1
        assert executor.hooks[0] is hook

    def test_register_multiple_hooks(self):
        """Should register multiple hooks in order."""
        executor = Executor()
        hook1 = MockHook()
        hook2 = MetricsHook()
        hook3 = MockHook()

        executor.register_hook(hook1)
        executor.register_hook(hook2)
        executor.register_hook(hook3)

        assert len(executor.hooks) == 3
        assert executor.hooks[0] is hook1
        assert executor.hooks[1] is hook2
        assert executor.hooks[2] is hook3

    def test_register_invalid_hook_raises_error(self):
        """Should raise TypeError for invalid hook."""
        executor = Executor()

        class InvalidHook:
            """Hook missing required methods."""

            pass

        with pytest.raises(TypeError, match="must implement ExecutorHook protocol"):
            executor.register_hook(InvalidHook())

    def test_register_hook_with_verbose(self, capsys):
        """Should print message when registering hook in verbose mode."""
        executor = Executor(verbose=True)
        hook = MockHook()

        executor.register_hook(hook)

        captured = capsys.readouterr()
        assert "MockHook" in captured.out


class TestHookExecution:
    """Test hook execution during agent runs."""

    @pytest.mark.asyncio
    async def test_hooks_called_during_execution(self, tmp_path):
        """Hooks should be called before and after agent execution."""
        # Create simple config
        config = WeaveConfig(
            agents={
                "test_agent": Agent(
                    name="test_agent",
                    model="gpt-4",
                    prompt="Test prompt",
                )
            },
            weaves={"test_weave": Weave(name="test_weave", agents=["test_agent"])},
        )

        # Create executor with hook
        hook = MockHook()
        executor = Executor(config=config)
        executor.register_hook(hook)

        # Build graph
        graph = DependencyGraph(config)
        graph.build("test_weave")

        # Execute in dry-run mode
        await executor.execute_flow(graph, "test_weave", dry_run=True)

        # Verify hooks were called
        assert "test_agent" in hook.before_calls
        assert "test_agent" in hook.after_calls

    @pytest.mark.asyncio
    async def test_multiple_hooks_called_in_order(self, tmp_path):
        """Multiple hooks should be called in registration order."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        hook1 = MockHook()
        hook2 = MockHook()
        hook3 = MockHook()

        executor = Executor(config=config)
        executor.register_hook(hook1)
        executor.register_hook(hook2)
        executor.register_hook(hook3)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # All hooks should be called
        assert hook1.before_calls == ["agent1"]
        assert hook2.before_calls == ["agent1"]
        assert hook3.before_calls == ["agent1"]

    @pytest.mark.asyncio
    async def test_metrics_hook_collects_data(self):
        """MetricsHook should collect execution metrics."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        metrics_hook = MetricsHook()
        executor = Executor(config=config)
        executor.register_hook(metrics_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # Verify metrics were collected
        assert "agent1" in metrics_hook.metrics
        assert "start_time" in metrics_hook.metrics["agent1"]
        assert "end_time" in metrics_hook.metrics["agent1"]
        assert "duration" in metrics_hook.metrics["agent1"]
        assert "model" in metrics_hook.metrics["agent1"]
        assert metrics_hook.metrics["agent1"]["model"] == "gpt-4"


class TestHookErrorHandling:
    """Test hook error handling."""

    @pytest.mark.asyncio
    async def test_hook_error_does_not_stop_execution(self):
        """Execution should continue even if hook fails."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        failing_hook = MockHook(should_fail=True)
        executor = Executor(config=config)
        executor.register_hook(failing_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        # Should not raise exception despite hook failure
        summary = await executor.execute_flow(graph, "test", dry_run=True)

        assert summary.successful == 1
        assert summary.failed == 0

    @pytest.mark.asyncio
    async def test_hook_error_logged_in_verbose_mode(self, capsys):
        """Hook errors should be logged in verbose mode."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        failing_hook = MockHook(should_fail=True)
        executor = Executor(config=config, verbose=True)
        executor.register_hook(failing_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        captured = capsys.readouterr()
        assert "Hook MockHook.before_agent() failed" in captured.out
        assert "Hook MockHook.after_agent() failed" in captured.out

    @pytest.mark.asyncio
    async def test_one_failing_hook_does_not_affect_others(self):
        """One failing hook should not prevent other hooks from running."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        good_hook = MockHook()
        failing_hook = MockHook(should_fail=True)
        another_good_hook = MockHook()

        executor = Executor(config=config)
        executor.register_hook(good_hook)
        executor.register_hook(failing_hook)
        executor.register_hook(another_good_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # Good hooks should still be called
        assert "agent1" in good_hook.before_calls
        assert "agent1" in good_hook.after_calls
        assert "agent1" in another_good_hook.before_calls
        assert "agent1" in another_good_hook.after_calls


class TestLoggingHook:
    """Test LoggingHook implementation."""

    @pytest.mark.asyncio
    async def test_logging_hook_creates_log_file(self, tmp_path):
        """LoggingHook should create and write to log file."""
        log_file = tmp_path / "test.log"

        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        logging_hook = LoggingHook(str(log_file))
        executor = Executor(config=config)
        executor.register_hook(logging_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # Verify log file was created and contains expected content
        assert log_file.exists()
        content = log_file.read_text()
        assert "[START] agent1 (gpt-4)" in content
        assert "[DONE] agent1" in content

    @pytest.mark.asyncio
    async def test_logging_hook_appends_to_existing_file(self, tmp_path):
        """LoggingHook should append to existing log file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Previous log entry\n")

        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        logging_hook = LoggingHook(str(log_file))
        executor = Executor(config=config)
        executor.register_hook(logging_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # Verify previous content preserved and new content appended
        content = log_file.read_text()
        assert "Previous log entry" in content
        assert "[START] agent1" in content

    @pytest.mark.asyncio
    async def test_logging_hook_records_execution_time(self, tmp_path):
        """LoggingHook should record execution time if available."""
        log_file = tmp_path / "test.log"

        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        logging_hook = LoggingHook(str(log_file))
        executor = Executor(config=config)
        executor.register_hook(logging_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        content = log_file.read_text()
        # Dry run includes execution_time
        assert "completed in" in content


class TestHookIntegration:
    """Integration tests for hooks with full executor."""

    @pytest.mark.asyncio
    async def test_hooks_with_multi_agent_workflow(self):
        """Hooks should work with multi-agent workflows."""
        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
                "agent2": Agent(
                    name="agent2", model="gpt-4", prompt="Test", inputs="agent1"
                ),
                "agent3": Agent(
                    name="agent3", model="gpt-4", prompt="Test", inputs="agent2"
                ),
            },
            weaves={"test": Weave(name="test", agents=["agent1", "agent2", "agent3"])},
        )

        hook = MockHook()
        executor = Executor(config=config)
        executor.register_hook(hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # All agents should have hooks called
        assert hook.before_calls == ["agent1", "agent2", "agent3"]
        assert hook.after_calls == ["agent1", "agent2", "agent3"]

    @pytest.mark.asyncio
    async def test_combined_logging_and_metrics_hooks(self, tmp_path):
        """Multiple hook types should work together."""
        log_file = tmp_path / "combined.log"

        config = WeaveConfig(
            agents={
                "agent1": Agent(name="agent1", model="gpt-4", prompt="Test"),
            },
            weaves={"test": Weave(name="test", agents=["agent1"])},
        )

        logging_hook = LoggingHook(str(log_file))
        metrics_hook = MetricsHook()

        executor = Executor(config=config)
        executor.register_hook(logging_hook)
        executor.register_hook(metrics_hook)

        graph = DependencyGraph(config)
        graph.build("test")

        await executor.execute_flow(graph, "test", dry_run=True)

        # Both hooks should have worked
        assert log_file.exists()
        assert "agent1" in metrics_hook.metrics
