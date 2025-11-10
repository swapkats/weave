"""Deployment manager for coordinating providers."""

from typing import Dict, Type, Optional, List
from rich.console import Console

from .provider import DeploymentProvider, DeploymentConfig, DeploymentInfo
from ..core.exceptions import WeaveError


class DeploymentError(WeaveError):
    """Deployment error."""

    pass


class DeploymentManager:
    """Manages deployment providers and coordinates deployments.

    The manager maintains a registry of available providers and
    routes deployment requests to the appropriate provider.
    """

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        """Initialize deployment manager.

        Args:
            console: Rich console for output
            verbose: Enable verbose logging
        """
        self.console = console or Console()
        self.verbose = verbose
        self.providers: Dict[str, Type[DeploymentProvider]] = {}

        # Auto-register built-in providers
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        """Register built-in deployment providers."""
        try:
            from .providers.aws import AWSProvider

            self.register_provider(AWSProvider)
        except ImportError:
            if self.verbose:
                self.console.print(
                    "[yellow]AWS provider not available (boto3 not installed)[/yellow]"
                )

        try:
            from .providers.gcp import GCPProvider

            self.register_provider(GCPProvider)
        except ImportError:
            if self.verbose:
                self.console.print(
                    "[yellow]GCP provider not available (google-cloud not installed)[/yellow]"
                )

        try:
            from .providers.docker import DockerProvider

            self.register_provider(DockerProvider)
        except ImportError:
            if self.verbose:
                self.console.print(
                    "[yellow]Docker provider not available (docker not installed)[/yellow]"
                )

    def register_provider(self, provider_class: Type[DeploymentProvider]) -> None:
        """Register a deployment provider.

        Args:
            provider_class: Provider class to register
        """
        # Instantiate to get the name
        instance = provider_class(console=self.console, verbose=self.verbose)
        self.providers[instance.name] = provider_class

        if self.verbose:
            self.console.print(f"[dim]Registered provider: {instance.name}[/dim]")

    def get_provider(self, name: str) -> DeploymentProvider:
        """Get a deployment provider by name.

        Args:
            name: Provider name (e.g., 'aws', 'gcp')

        Returns:
            Provider instance

        Raises:
            DeploymentError: If provider not found
        """
        if name not in self.providers:
            available = ", ".join(sorted(self.providers.keys()))
            raise DeploymentError(
                f"Unknown deployment provider: {name}",
                suggestion=f"Available providers: {available}",
            )

        return self.providers[name](console=self.console, verbose=self.verbose)

    def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy using the specified provider.

        Args:
            config: Deployment configuration

        Returns:
            Deployment information

        Raises:
            DeploymentError: If deployment fails
        """
        provider = self.get_provider(config.provider)

        # Validate configuration
        try:
            provider.validate_config(config)
        except Exception as e:
            raise DeploymentError(
                f"Invalid deployment configuration: {e}",
                suggestion="Check your deployment configuration in .weave.yaml",
            )

        # Execute deployment
        self.console.print(
            f"\n🚀 [bold cyan]Deploying to {config.provider}:[/bold cyan] {config.name}\n"
        )

        try:
            info = provider.deploy(config)
            self.console.print(f"\n✅ [green]Deployment successful![/green]")

            if info.endpoint:
                self.console.print(f"[bold]Endpoint:[/bold] {info.endpoint}")

            return info

        except Exception as e:
            raise DeploymentError(
                f"Deployment failed: {e}",
                suggestion=f"Check {config.provider} credentials and configuration",
            )

    def status(self, provider_name: str, deployment_name: str) -> DeploymentInfo:
        """Get deployment status.

        Args:
            provider_name: Provider name
            deployment_name: Deployment name

        Returns:
            Deployment information
        """
        provider = self.get_provider(provider_name)
        return provider.status(deployment_name)

    def destroy(self, provider_name: str, deployment_name: str) -> bool:
        """Destroy a deployment.

        Args:
            provider_name: Provider name
            deployment_name: Deployment name

        Returns:
            True if destroyed successfully
        """
        provider = self.get_provider(provider_name)

        self.console.print(
            f"\n🗑️  [bold red]Destroying deployment:[/bold red] {deployment_name}\n"
        )

        try:
            success = provider.destroy(deployment_name)
            if success:
                self.console.print(f"\n✅ [green]Deployment destroyed[/green]")
            return success

        except Exception as e:
            raise DeploymentError(f"Failed to destroy deployment: {e}")

    def list_deployments(
        self, provider_name: Optional[str] = None
    ) -> Dict[str, List[DeploymentInfo]]:
        """List all deployments.

        Args:
            provider_name: Optional provider name to filter by

        Returns:
            Dictionary mapping provider name to list of deployments
        """
        results = {}

        if provider_name:
            provider = self.get_provider(provider_name)
            results[provider_name] = provider.list_deployments()
        else:
            # List from all providers
            for name in self.providers.keys():
                try:
                    provider = self.get_provider(name)
                    deployments = provider.list_deployments()
                    if deployments:
                        results[name] = deployments
                except Exception as e:
                    if self.verbose:
                        self.console.print(
                            f"[yellow]Could not list {name} deployments: {e}[/yellow]"
                        )

        return results
