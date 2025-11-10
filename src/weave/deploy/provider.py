"""Base deployment provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class DeploymentStatus(str, Enum):
    """Deployment status."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class DeploymentConfig(BaseModel):
    """Configuration for deployment.

    This is the base configuration that all providers extend.
    Provider-specific config goes in the 'config' dict.
    """

    name: str = Field(..., description="Deployment name")
    provider: str = Field(..., description="Provider name (aws, gcp, docker, etc.)")
    region: Optional[str] = Field(None, description="Cloud region")
    environment: str = Field("production", description="Environment (dev, staging, production)")
    config_file: str = Field(".weave.yaml", description="Path to Weave config file")

    # Provider-specific configuration
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )

    # Resource allocation
    memory_mb: int = Field(512, description="Memory allocation in MB")
    timeout_seconds: int = Field(300, description="Execution timeout in seconds")

    # Environment variables
    env_vars: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables for deployment"
    )


class DeploymentInfo(BaseModel):
    """Information about a deployment."""

    name: str
    provider: str
    status: DeploymentStatus
    endpoint: Optional[str] = None
    region: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeploymentProvider(ABC):
    """Abstract base class for deployment providers.

    Extend this class to add support for new cloud providers or deployment targets.

    Example:
        ```python
        class MyCloudProvider(DeploymentProvider):
            def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
                # Implement deployment logic
                pass
        ```
    """

    def __init__(self, console=None, verbose: bool = False):
        """Initialize provider.

        Args:
            console: Rich console for output
            verbose: Enable verbose logging
        """
        from rich.console import Console

        self.console = console or Console()
        self.verbose = verbose

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'aws', 'gcp', 'docker')."""
        pass

    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy Weave to the provider.

        Args:
            config: Deployment configuration

        Returns:
            Deployment information

        Raises:
            DeploymentError: If deployment fails
        """
        pass

    @abstractmethod
    def status(self, deployment_name: str) -> DeploymentInfo:
        """Get deployment status.

        Args:
            deployment_name: Name of the deployment

        Returns:
            Deployment information

        Raises:
            DeploymentError: If status check fails
        """
        pass

    @abstractmethod
    def destroy(self, deployment_name: str) -> bool:
        """Destroy deployment.

        Args:
            deployment_name: Name of the deployment

        Returns:
            True if destroyed successfully

        Raises:
            DeploymentError: If destruction fails
        """
        pass

    @abstractmethod
    def list_deployments(self) -> List[DeploymentInfo]:
        """List all deployments managed by this provider.

        Returns:
            List of deployment information
        """
        pass

    @abstractmethod
    def validate_config(self, config: DeploymentConfig) -> bool:
        """Validate deployment configuration.

        Args:
            config: Deployment configuration to validate

        Returns:
            True if valid

        Raises:
            ConfigError: If configuration is invalid
        """
        pass

    def log(self, message: str, style: str = ""):
        """Log a message if verbose mode is enabled.

        Args:
            message: Message to log
            style: Rich style string
        """
        if self.verbose:
            if style:
                self.console.print(f"[{style}]{message}[/{style}]")
            else:
                self.console.print(message)
