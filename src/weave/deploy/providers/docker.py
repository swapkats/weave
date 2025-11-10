"""Docker deployment provider for containerized execution."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import shutil

from ..provider import DeploymentProvider, DeploymentConfig, DeploymentInfo, DeploymentStatus
from ..auth import AuthenticationManager, AuthConfig
from ...core.exceptions import WeaveError


class DockerProvider(DeploymentProvider):
    """Deploy Weave as a Docker container.

    Supports:
    - Local Docker daemon
    - Docker registries (Docker Hub, GCR, ECR, etc.)
    - Docker Compose for multi-container setups
    """

    def __init__(self, console=None, verbose: bool = False):
        """Initialize Docker provider."""
        super().__init__(console, verbose)
        self.auth_manager = AuthenticationManager()
        self._docker_client = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "docker"

    def _init_client(self, credentials: Dict[str, Any]) -> None:
        """Initialize Docker client.

        Args:
            credentials: Docker credentials
        """
        try:
            import docker

            self._docker_client = docker.from_env()

            # Login to registry if credentials provided
            if credentials.get("registry_url") and credentials.get("username"):
                self.log(
                    f"Logging into registry: {credentials['registry_url']}", "dim"
                )
                self._docker_client.login(
                    username=credentials["username"],
                    password=credentials.get("password", ""),
                    registry=credentials["registry_url"],
                )

        except ImportError:
            raise WeaveError(
                "docker library not installed",
                suggestion="Install with: pip install weave-cli[docker] or pip install docker",
            )
        except Exception as e:
            raise WeaveError(
                f"Could not connect to Docker daemon: {e}",
                suggestion="Ensure Docker is running and accessible",
            )

    def validate_config(self, config: DeploymentConfig) -> bool:
        """Validate Docker deployment configuration.

        Args:
            config: Deployment configuration

        Returns:
            True if valid
        """
        # Get credentials
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="docker")

        # Initialize client to verify Docker is available
        self._init_client(credentials)

        return True

    def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy to Docker.

        Args:
            config: Deployment configuration

        Returns:
            Deployment information
        """
        # Get credentials and initialize client
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="docker")
        self._init_client(credentials)

        self.log(f"Building Docker image: {config.name}")

        # Build Docker image
        image_tag = self._build_image(config, credentials)

        # Push to registry if configured
        if credentials.get("registry_url"):
            self.log(f"Pushing to registry: {credentials['registry_url']}", "dim")
            self._push_image(image_tag, credentials)

        # Run container if requested
        container = None
        endpoint = None
        if config.config.get("run", True):
            self.log("Starting container...", "dim")
            container = self._run_container(config, image_tag)

            # Get container endpoint
            if config.config.get("port"):
                endpoint = f"http://localhost:{config.config['port']}"

        return DeploymentInfo(
            name=config.name,
            provider="docker",
            status=DeploymentStatus.ACTIVE,
            endpoint=endpoint,
            metadata={
                "image": image_tag,
                "container_id": container.id if container else None,
                "registry": credentials.get("registry_url"),
            },
        )

    def _build_image(self, config: DeploymentConfig, credentials: Dict[str, Any]) -> str:
        """Build Docker image.

        Args:
            config: Deployment configuration
            credentials: Docker credentials

        Returns:
            Image tag
        """
        # Create temporary build context
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Copy Weave config
            config_path = Path(config.config_file)
            if config_path.exists():
                shutil.copy(config_path, tmp_path / ".weave.yaml")

            # Create Dockerfile
            dockerfile = self._generate_dockerfile(config)
            (tmp_path / "Dockerfile").write_text(dockerfile)

            # Create entrypoint script
            entrypoint = '''#!/bin/sh
set -e

# Run Weave
weave apply --real ${WEAVE_NAME:+--weave $WEAVE_NAME}
'''
            (tmp_path / "entrypoint.sh").write_text(entrypoint)

            # Build image
            registry = credentials.get("registry_url", "")
            if registry:
                image_tag = f"{registry}/{config.name}:latest"
            else:
                image_tag = f"{config.name}:latest"

            self.log(f"Building image: {image_tag}", "dim")

            try:
                image, build_logs = self._docker_client.images.build(
                    path=str(tmp_path), tag=image_tag, rm=True
                )

                if self.verbose:
                    for log in build_logs:
                        if "stream" in log:
                            self.console.print(f"[dim]{log['stream'].strip()}[/dim]")

                return image_tag

            except Exception as e:
                raise WeaveError(f"Docker build failed: {e}", suggestion="Check Dockerfile and dependencies")

    def _generate_dockerfile(self, config: DeploymentConfig) -> str:
        """Generate Dockerfile for Weave.

        Args:
            config: Deployment configuration

        Returns:
            Dockerfile content
        """
        # Base Python version
        python_version = config.config.get("python_version", "3.11")

        dockerfile = f"""# Weave Docker Image
FROM python:{python_version}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Weave configuration
COPY .weave.yaml /app/.weave.yaml

# Install Weave with LLM support
RUN pip install --no-cache-dir weave-cli[llm]

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
"""

        # Add custom environment variables
        for key, value in config.env_vars.items():
            dockerfile += f'ENV {key}="{value}"\n'

        # Add entrypoint
        dockerfile += "\nENTRYPOINT ['/app/entrypoint.sh']\n"

        return dockerfile

    def _push_image(self, image_tag: str, credentials: Dict[str, Any]) -> None:
        """Push image to registry.

        Args:
            image_tag: Image tag
            credentials: Registry credentials
        """
        try:
            for line in self._docker_client.images.push(image_tag, stream=True, decode=True):
                if self.verbose and "status" in line:
                    self.console.print(f"[dim]{line['status']}[/dim]")

        except Exception as e:
            raise WeaveError(
                f"Docker push failed: {e}",
                suggestion="Check registry credentials and network connection",
            )

    def _run_container(self, config: DeploymentConfig, image_tag: str):
        """Run Docker container.

        Args:
            config: Deployment configuration
            image_tag: Image tag

        Returns:
            Container object
        """
        # Container configuration
        container_config = {
            "image": image_tag,
            "name": config.name,
            "detach": True,
            "environment": config.env_vars,
        }

        # Port mapping if specified
        if config.config.get("port"):
            container_config["ports"] = {
                f"{config.config['port']}/tcp": config.config["port"]
            }

        # Volume mounts if specified
        if config.config.get("volumes"):
            container_config["volumes"] = config.config["volumes"]

        try:
            # Remove existing container if it exists
            try:
                old_container = self._docker_client.containers.get(config.name)
                old_container.remove(force=True)
            except:
                pass

            # Run new container
            container = self._docker_client.containers.run(**container_config)
            return container

        except Exception as e:
            raise WeaveError(f"Failed to run container: {e}", suggestion="Check Docker daemon and image")

    def status(self, deployment_name: str) -> DeploymentInfo:
        """Get Docker container status.

        Args:
            deployment_name: Container name

        Returns:
            Deployment information
        """
        # Initialize client
        credentials = self.auth_manager.get_credentials(provider_name="docker")
        self._init_client(credentials)

        try:
            container = self._docker_client.containers.get(deployment_name)

            # Map container status
            status_map = {
                "created": DeploymentStatus.PENDING,
                "running": DeploymentStatus.ACTIVE,
                "paused": DeploymentStatus.ACTIVE,
                "restarting": DeploymentStatus.DEPLOYING,
                "removing": DeploymentStatus.DESTROYING,
                "exited": DeploymentStatus.FAILED,
                "dead": DeploymentStatus.FAILED,
            }

            status = status_map.get(container.status, DeploymentStatus.ACTIVE)

            return DeploymentInfo(
                name=deployment_name,
                provider="docker",
                status=status,
                metadata={
                    "container_id": container.id,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "created": container.attrs.get("Created"),
                },
            )

        except Exception as e:
            raise WeaveError(
                f"Container not found: {deployment_name}",
                suggestion="Check container name with 'docker ps -a'",
            )

    def destroy(self, deployment_name: str) -> bool:
        """Destroy Docker container.

        Args:
            deployment_name: Container name

        Returns:
            True if destroyed
        """
        # Initialize client
        credentials = self.auth_manager.get_credentials(provider_name="docker")
        self._init_client(credentials)

        try:
            container = self._docker_client.containers.get(deployment_name)
            container.remove(force=True)

            # Also remove the image if requested
            # (For now we keep images to allow redeployment)

            return True

        except Exception as e:
            if "No such container" in str(e):
                return True  # Already removed
            raise

    def list_deployments(self) -> List[DeploymentInfo]:
        """List all Docker containers.

        Returns:
            List of deployment information
        """
        # Initialize client
        credentials = self.auth_manager.get_credentials(provider_name="docker")
        self._init_client(credentials)

        deployments = []

        try:
            # List all containers (including stopped)
            containers = self._docker_client.containers.list(all=True)

            for container in containers:
                # Only include Weave deployments
                if "weave" in container.name.lower():
                    status_map = {
                        "created": DeploymentStatus.PENDING,
                        "running": DeploymentStatus.ACTIVE,
                        "exited": DeploymentStatus.FAILED,
                    }

                    deployments.append(
                        DeploymentInfo(
                            name=container.name,
                            provider="docker",
                            status=status_map.get(container.status, DeploymentStatus.ACTIVE),
                            metadata={
                                "container_id": container.id,
                                "image": container.image.tags[0]
                                if container.image.tags
                                else "unknown",
                                "status": container.status,
                            },
                        )
                    )

        except Exception as e:
            self.log(f"Error listing deployments: {e}", "yellow")

        return deployments
