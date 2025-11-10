"""GCP deployment provider for Cloud Functions and Cloud Run."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import tempfile
import shutil
import subprocess

from ..provider import DeploymentProvider, DeploymentConfig, DeploymentInfo, DeploymentStatus
from ..auth import AuthenticationManager, AuthConfig
from ...core.exceptions import WeaveError


class GCPProvider(DeploymentProvider):
    """Deploy Weave to Google Cloud Platform.

    Supports:
    - Cloud Functions (Gen 2) for serverless execution
    - Cloud Run for containerized execution
    """

    def __init__(self, console=None, verbose: bool = False):
        """Initialize GCP provider."""
        super().__init__(console, verbose)
        self.auth_manager = AuthenticationManager()
        self._functions_client = None
        self._run_client = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "gcp"

    def _init_clients(self, credentials: Dict[str, Any]) -> None:
        """Initialize GCP clients.

        Args:
            credentials: GCP credentials
        """
        try:
            from google.cloud import functions_v2
            from google.cloud import run_v2
            from google.oauth2 import service_account
            import google.auth

            # Set up authentication
            if credentials.get("credentials_file"):
                creds = service_account.Credentials.from_service_account_file(
                    credentials["credentials_file"]
                )
                self._credentials = creds
            else:
                # Use default credentials
                self._credentials, _ = google.auth.default()

            # Initialize clients
            self._functions_client = functions_v2.FunctionServiceClient(
                credentials=self._credentials
            )
            self._run_client = run_v2.ServicesClient(credentials=self._credentials)

            self._project_id = credentials.get("project_id")
            if not self._project_id and credentials.get("credentials_file"):
                # Extract from service account
                with open(credentials["credentials_file"]) as f:
                    sa_data = json.load(f)
                    self._project_id = sa_data.get("project_id")

        except ImportError:
            raise WeaveError(
                "google-cloud libraries not installed",
                suggestion="Install with: pip install weave-cli[gcp] or pip install google-cloud-functions google-cloud-run",
            )

    def validate_config(self, config: DeploymentConfig) -> bool:
        """Validate GCP deployment configuration.

        Args:
            config: Deployment configuration

        Returns:
            True if valid
        """
        # Get credentials
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="gcp")

        # Validate project ID
        if not credentials.get("project_id") and not credentials.get("credentials_file"):
            raise WeaveError(
                "GCP project ID required",
                suggestion="Set GCP_PROJECT_ID environment variable or provide in config",
            )

        # Validate deployment type
        deploy_type = config.config.get("type", "function")
        if deploy_type not in ["function", "run"]:
            raise WeaveError(
                f"Invalid GCP deployment type: {deploy_type}",
                suggestion="Use 'function' or 'run'",
            )

        return True

    def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy to GCP.

        Args:
            config: Deployment configuration

        Returns:
            Deployment information
        """
        # Get credentials and initialize clients
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="gcp")
        self._init_clients(credentials)

        # Choose deployment type
        deploy_type = config.config.get("type", "function")

        if deploy_type == "function":
            return self._deploy_cloud_function(config, credentials)
        elif deploy_type == "run":
            return self._deploy_cloud_run(config, credentials)
        else:
            raise WeaveError(f"Unknown deployment type: {deploy_type}")

    def _deploy_cloud_function(
        self, config: DeploymentConfig, credentials: Dict[str, Any]
    ) -> DeploymentInfo:
        """Deploy to Cloud Functions (Gen 2).

        Args:
            config: Deployment configuration
            credentials: GCP credentials

        Returns:
            Deployment information
        """
        self.log(f"Deploying to Cloud Functions: {config.name}")

        # Create temporary directory for function source
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Copy Weave config
            config_path = Path(config.config_file)
            if config_path.exists():
                shutil.copy(config_path, tmp_path / ".weave.yaml")

            # Create main.py (Cloud Functions entry point)
            main_code = '''"""Cloud Function handler for Weave."""
import functions_framework
import json
from weave.parser.config import load_config_from_path
from weave.runtime.real_executor import RealExecutor
import asyncio

@functions_framework.http
def weave_handler(request):
    """Handle Cloud Function HTTP request."""
    # Parse request
    request_json = request.get_json(silent=True)
    weave_name = request_json.get("weave") if request_json else None

    # Load Weave config
    config = load_config_from_path(".weave.yaml")

    # Get weave name
    if not weave_name:
        weave_name = list(config.weaves.keys())[0]

    # Execute
    from weave.core.graph import DependencyGraph
    graph = DependencyGraph(config)
    executor = RealExecutor(config=config)
    result = asyncio.run(executor.execute_flow(graph, weave_name, dry_run=False))

    # Return results
    return {
        "weave": result.weave_name,
        "successful": result.successful,
        "failed": result.failed,
        "total_time": result.total_time,
    }
'''
            (tmp_path / "main.py").write_text(main_code)

            # Create requirements.txt
            requirements = """weave-cli[llm]
functions-framework>=3.0.0
"""
            (tmp_path / "requirements.txt").write_text(requirements)

            # Deploy using gcloud CLI
            self.log("Deploying function...", "dim")
            result = self._deploy_with_gcloud(
                config.name,
                tmp_path,
                config.region or "us-central1",
                self._project_id,
                config.memory_mb,
                config.timeout_seconds,
                config.env_vars,
            )

            return DeploymentInfo(
                name=config.name,
                provider="gcp",
                status=DeploymentStatus.ACTIVE,
                endpoint=result.get("url"),
                region=config.region or "us-central1",
                metadata={
                    "deployment_type": "function",
                    "project_id": self._project_id,
                },
            )

    def _deploy_with_gcloud(
        self,
        name: str,
        source_dir: Path,
        region: str,
        project_id: str,
        memory_mb: int,
        timeout_seconds: int,
        env_vars: Dict[str, str],
    ) -> Dict[str, Any]:
        """Deploy using gcloud CLI.

        Args:
            name: Function name
            source_dir: Source directory
            region: GCP region
            project_id: Project ID
            memory_mb: Memory allocation
            timeout_seconds: Timeout
            env_vars: Environment variables

        Returns:
            Deployment result with URL
        """
        # Build gcloud command
        cmd = [
            "gcloud",
            "functions",
            "deploy",
            name,
            f"--gen2",
            f"--runtime=python311",
            f"--region={region}",
            f"--source={source_dir}",
            f"--entry-point=weave_handler",
            f"--trigger-http",
            f"--allow-unauthenticated",
            f"--memory={memory_mb}MB",
            f"--timeout={timeout_seconds}s",
            f"--project={project_id}",
        ]

        # Add environment variables
        if env_vars:
            env_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])
            cmd.append(f"--set-env-vars={env_str}")

        # Run deployment
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=source_dir
            )

            if self.verbose:
                self.console.print(f"[dim]{result.stdout}[/dim]")

            # Extract URL from output
            url = None
            for line in result.stdout.split("\n"):
                if "url:" in line.lower() or "https://" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("https://"):
                            url = part
                            break

            return {"url": url, "output": result.stdout}

        except subprocess.CalledProcessError as e:
            raise WeaveError(
                f"gcloud deployment failed: {e.stderr}",
                suggestion="Ensure gcloud CLI is installed and authenticated",
            )
        except FileNotFoundError:
            raise WeaveError(
                "gcloud CLI not found",
                suggestion="Install gcloud CLI: https://cloud.google.com/sdk/docs/install",
            )

    def _deploy_cloud_run(
        self, config: DeploymentConfig, credentials: Dict[str, Any]
    ) -> DeploymentInfo:
        """Deploy to Cloud Run.

        Args:
            config: Deployment configuration
            credentials: GCP credentials

        Returns:
            Deployment information
        """
        raise WeaveError(
            "Cloud Run deployment not yet implemented",
            suggestion="Use Cloud Functions deployment for now",
        )

    def status(self, deployment_name: str) -> DeploymentInfo:
        """Get Cloud Function deployment status.

        Args:
            deployment_name: Function name

        Returns:
            Deployment information
        """
        # Initialize clients
        credentials = self.auth_manager.get_credentials(provider_name="gcp")
        self._init_clients(credentials)

        # Use gcloud to get status
        try:
            cmd = [
                "gcloud",
                "functions",
                "describe",
                deployment_name,
                f"--gen2",
                f"--region={credentials.get('region', 'us-central1')}",
                f"--project={self._project_id}",
                "--format=json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Parse status
            state = data.get("state", "ACTIVE")
            status_map = {
                "ACTIVE": DeploymentStatus.ACTIVE,
                "DEPLOYING": DeploymentStatus.DEPLOYING,
                "FAILED": DeploymentStatus.FAILED,
                "DELETING": DeploymentStatus.DESTROYING,
            }

            return DeploymentInfo(
                name=deployment_name,
                provider="gcp",
                status=status_map.get(state, DeploymentStatus.ACTIVE),
                endpoint=data.get("serviceConfig", {}).get("uri"),
                region=credentials.get("region", "us-central1"),
                metadata={
                    "project_id": self._project_id,
                    "state": state,
                    "update_time": data.get("updateTime"),
                },
            )

        except subprocess.CalledProcessError:
            raise WeaveError(
                f"Deployment not found: {deployment_name}",
                suggestion="Check deployment name, region, and project ID",
            )

    def destroy(self, deployment_name: str) -> bool:
        """Destroy Cloud Function deployment.

        Args:
            deployment_name: Function name

        Returns:
            True if destroyed
        """
        # Initialize clients
        credentials = self.auth_manager.get_credentials(provider_name="gcp")
        self._init_clients(credentials)

        try:
            cmd = [
                "gcloud",
                "functions",
                "delete",
                deployment_name,
                f"--gen2",
                f"--region={credentials.get('region', 'us-central1')}",
                f"--project={self._project_id}",
                "--quiet",
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True

        except subprocess.CalledProcessError as e:
            if "NOT_FOUND" in e.stderr:
                return True  # Already deleted
            raise

    def list_deployments(self) -> List[DeploymentInfo]:
        """List all Cloud Function deployments.

        Returns:
            List of deployment information
        """
        # Initialize clients
        credentials = self.auth_manager.get_credentials(provider_name="gcp")
        self._init_clients(credentials)

        deployments = []

        try:
            cmd = [
                "gcloud",
                "functions",
                "list",
                f"--gen2",
                f"--project={self._project_id}",
                "--format=json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            functions = json.loads(result.stdout)

            for func in functions:
                # Only include Weave deployments
                if "weave" in func.get("name", "").lower():
                    state = func.get("state", "ACTIVE")
                    status_map = {
                        "ACTIVE": DeploymentStatus.ACTIVE,
                        "DEPLOYING": DeploymentStatus.DEPLOYING,
                        "FAILED": DeploymentStatus.FAILED,
                    }

                    deployments.append(
                        DeploymentInfo(
                            name=func["name"].split("/")[-1],
                            provider="gcp",
                            status=status_map.get(state, DeploymentStatus.ACTIVE),
                            endpoint=func.get("serviceConfig", {}).get("uri"),
                            region=func.get("environment", {}).get("region"),
                            metadata={
                                "project_id": self._project_id,
                                "update_time": func.get("updateTime"),
                            },
                        )
                    )

        except Exception as e:
            self.log(f"Error listing deployments: {e}", "yellow")

        return deployments
