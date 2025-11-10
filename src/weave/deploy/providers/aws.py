"""AWS deployment provider for Lambda and ECS."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import zipfile
import io
import time

from ..provider import DeploymentProvider, DeploymentConfig, DeploymentInfo, DeploymentStatus
from ..auth import AuthenticationManager, AuthConfig
from ...core.exceptions import WeaveError


class AWSProvider(DeploymentProvider):
    """Deploy Weave to AWS Lambda or ECS.

    Supports:
    - AWS Lambda for serverless execution
    - AWS ECS for containerized execution
    - API Gateway for HTTP endpoints
    """

    def __init__(self, console=None, verbose: bool = False):
        """Initialize AWS provider."""
        super().__init__(console, verbose)
        self.auth_manager = AuthenticationManager()
        self._boto3 = None
        self._lambda_client = None
        self._ecs_client = None
        self._apigateway_client = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "aws"

    def _init_clients(self, credentials: Dict[str, Any]) -> None:
        """Initialize AWS clients.

        Args:
            credentials: AWS credentials
        """
        try:
            import boto3
            from botocore.exceptions import ClientError

            self._boto3 = boto3
            self._client_error = ClientError

            # Create session with credentials
            session_kwargs = {}
            if credentials.get("access_key_id"):
                session_kwargs["aws_access_key_id"] = credentials["access_key_id"]
            if credentials.get("secret_access_key"):
                session_kwargs["aws_secret_access_key"] = credentials["secret_access_key"]
            if credentials.get("session_token"):
                session_kwargs["aws_session_token"] = credentials["session_token"]
            if credentials.get("region"):
                session_kwargs["region_name"] = credentials["region"]

            session = boto3.Session(**session_kwargs)

            # Initialize clients
            self._lambda_client = session.client("lambda")
            self._ecs_client = session.client("ecs")
            self._apigateway_client = session.client("apigatewayv2")
            self._iam_client = session.client("iam")

        except ImportError:
            raise WeaveError(
                "boto3 is not installed",
                suggestion="Install with: pip install weave-cli[aws] or pip install boto3",
            )

    def validate_config(self, config: DeploymentConfig) -> bool:
        """Validate AWS deployment configuration.

        Args:
            config: Deployment configuration

        Returns:
            True if valid
        """
        # Get credentials
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="aws")

        # Validate credentials
        required_keys = ["region"]
        if credentials.get("access_key_id"):
            required_keys.extend(["access_key_id", "secret_access_key"])

        self.auth_manager.validate_credentials(credentials, required_keys)

        # Validate deployment type
        deploy_type = config.config.get("type", "lambda")
        if deploy_type not in ["lambda", "ecs"]:
            raise WeaveError(
                f"Invalid AWS deployment type: {deploy_type}",
                suggestion="Use 'lambda' or 'ecs'",
            )

        return True

    def deploy(self, config: DeploymentConfig) -> DeploymentInfo:
        """Deploy to AWS.

        Args:
            config: Deployment configuration

        Returns:
            Deployment information
        """
        # Get credentials and initialize clients
        auth_config = config.config.get("auth")
        if isinstance(auth_config, dict):
            auth_config = AuthConfig(**auth_config)

        credentials = self.auth_manager.get_credentials(auth_config, provider_name="aws")
        self._init_clients(credentials)

        # Choose deployment type
        deploy_type = config.config.get("type", "lambda")

        if deploy_type == "lambda":
            return self._deploy_lambda(config, credentials)
        elif deploy_type == "ecs":
            return self._deploy_ecs(config, credentials)
        else:
            raise WeaveError(f"Unknown deployment type: {deploy_type}")

    def _deploy_lambda(self, config: DeploymentConfig, credentials: Dict[str, Any]) -> DeploymentInfo:
        """Deploy to AWS Lambda.

        Args:
            config: Deployment configuration
            credentials: AWS credentials

        Returns:
            Deployment information
        """
        self.log(f"Deploying to AWS Lambda: {config.name}")

        # Create deployment package
        self.log("Creating deployment package...", "dim")
        zip_data = self._create_lambda_package(config)

        # Get or create IAM role
        self.log("Setting up IAM role...", "dim")
        role_arn = self._get_or_create_lambda_role(config.name)

        # Create or update Lambda function
        try:
            # Try to get existing function
            response = self._lambda_client.get_function(FunctionName=config.name)
            function_arn = response["Configuration"]["FunctionArn"]

            # Update existing function
            self.log("Updating existing Lambda function...", "dim")
            self._lambda_client.update_function_code(
                FunctionName=config.name, ZipFile=zip_data
            )

            # Update configuration
            self._lambda_client.update_function_configuration(
                FunctionName=config.name,
                Runtime="python3.11",
                Handler="lambda_handler.handler",
                Role=role_arn,
                MemorySize=config.memory_mb,
                Timeout=config.timeout_seconds,
                Environment={"Variables": config.env_vars},
            )

        except self._client_error as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                # Create new function
                self.log("Creating new Lambda function...", "dim")
                response = self._lambda_client.create_function(
                    FunctionName=config.name,
                    Runtime="python3.11",
                    Role=role_arn,
                    Handler="lambda_handler.handler",
                    Code={"ZipFile": zip_data},
                    MemorySize=config.memory_mb,
                    Timeout=config.timeout_seconds,
                    Environment={"Variables": config.env_vars},
                )
                function_arn = response["FunctionArn"]
            else:
                raise

        # Wait for function to be active
        self.log("Waiting for function to be ready...", "dim")
        time.sleep(2)

        # Create API Gateway if requested
        endpoint = None
        if config.config.get("create_api", True):
            self.log("Creating API Gateway...", "dim")
            endpoint = self._create_api_gateway(config.name, function_arn, credentials["region"])

        return DeploymentInfo(
            name=config.name,
            provider="aws",
            status=DeploymentStatus.ACTIVE,
            endpoint=endpoint,
            region=credentials["region"],
            metadata={
                "function_arn": function_arn,
                "deployment_type": "lambda",
            },
        )

    def _create_lambda_package(self, config: DeploymentConfig) -> bytes:
        """Create Lambda deployment package.

        Args:
            config: Deployment configuration

        Returns:
            Zip file bytes
        """
        # Create in-memory zip file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add Weave config
            config_path = Path(config.config_file)
            if config_path.exists():
                zip_file.write(config_path, ".weave.yaml")

            # Add Lambda handler
            handler_code = '''"""Lambda handler for Weave."""
import json
from weave.parser.config import load_config_from_path
from weave.runtime.real_executor import RealExecutor

def handler(event, context):
    """Handle Lambda invocation."""
    # Load Weave config
    config = load_config_from_path(".weave.yaml")

    # Execute weave
    from weave.core.graph import DependencyGraph
    import asyncio

    # Get weave name from event or use first weave
    weave_name = event.get("weave") or list(config.weaves.keys())[0]
    graph = DependencyGraph(config)

    # Execute
    executor = RealExecutor(config=config)
    result = asyncio.run(executor.execute_flow(graph, weave_name, dry_run=False))

    # Return results
    return {
        "statusCode": 200,
        "body": json.dumps({
            "weave": result.weave_name,
            "successful": result.successful,
            "failed": result.failed,
            "total_time": result.total_time,
        })
    }
'''
            zip_file.writestr("lambda_handler.py", handler_code)

        return zip_buffer.getvalue()

    def _get_or_create_lambda_role(self, function_name: str) -> str:
        """Get or create IAM role for Lambda.

        Args:
            function_name: Lambda function name

        Returns:
            Role ARN
        """
        role_name = f"weave-lambda-{function_name}"

        try:
            response = self._iam_client.get_role(RoleName=role_name)
            return response["Role"]["Arn"]
        except self._client_error as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                # Create role
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }

                response = self._iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                )

                # Attach basic Lambda execution policy
                self._iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                )

                # Wait for role to be available
                time.sleep(10)

                return response["Role"]["Arn"]
            else:
                raise

    def _create_api_gateway(self, function_name: str, function_arn: str, region: str) -> str:
        """Create API Gateway for Lambda function.

        Args:
            function_name: Lambda function name
            function_arn: Lambda function ARN
            region: AWS region

        Returns:
            API endpoint URL
        """
        api_name = f"weave-{function_name}"

        try:
            # Create HTTP API
            response = self._apigateway_client.create_api(
                Name=api_name, ProtocolType="HTTP", Target=function_arn
            )

            api_id = response["ApiId"]
            endpoint = response["ApiEndpoint"]

            # Add Lambda permission for API Gateway
            self._lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"apigateway-{api_id}",
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{region}:*:{api_id}/*",
            )

            return endpoint

        except Exception as e:
            self.log(f"Warning: Could not create API Gateway: {e}", "yellow")
            return None

    def _deploy_ecs(self, config: DeploymentConfig, credentials: Dict[str, Any]) -> DeploymentInfo:
        """Deploy to AWS ECS.

        Args:
            config: Deployment configuration
            credentials: AWS credentials

        Returns:
            Deployment information
        """
        raise WeaveError(
            "ECS deployment not yet implemented", suggestion="Use Lambda deployment for now"
        )

    def status(self, deployment_name: str) -> DeploymentInfo:
        """Get Lambda deployment status.

        Args:
            deployment_name: Function name

        Returns:
            Deployment information
        """
        # Initialize clients with default credentials
        credentials = self.auth_manager.get_credentials(provider_name="aws")
        self._init_clients(credentials)

        try:
            response = self._lambda_client.get_function(FunctionName=deployment_name)

            config = response["Configuration"]
            state = config.get("State", "Active")

            # Map Lambda state to deployment status
            status_map = {
                "Pending": DeploymentStatus.DEPLOYING,
                "Active": DeploymentStatus.ACTIVE,
                "Failed": DeploymentStatus.FAILED,
            }

            return DeploymentInfo(
                name=deployment_name,
                provider="aws",
                status=status_map.get(state, DeploymentStatus.ACTIVE),
                region=credentials["region"],
                metadata={
                    "function_arn": config["FunctionArn"],
                    "runtime": config["Runtime"],
                    "memory": config["MemorySize"],
                    "timeout": config["Timeout"],
                    "last_modified": config["LastModified"],
                },
            )

        except self._client_error as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise WeaveError(
                    f"Deployment not found: {deployment_name}",
                    suggestion="Check deployment name and region",
                )
            raise

    def destroy(self, deployment_name: str) -> bool:
        """Destroy Lambda deployment.

        Args:
            deployment_name: Function name

        Returns:
            True if destroyed
        """
        # Initialize clients
        credentials = self.auth_manager.get_credentials(provider_name="aws")
        self._init_clients(credentials)

        try:
            # Delete Lambda function
            self._lambda_client.delete_function(FunctionName=deployment_name)

            # Try to delete associated API Gateway
            try:
                apis = self._apigateway_client.get_apis()
                for api in apis.get("Items", []):
                    if api["Name"] == f"weave-{deployment_name}":
                        self._apigateway_client.delete_api(ApiId=api["ApiId"])
            except Exception as e:
                self.log(f"Could not delete API Gateway: {e}", "yellow")

            # Try to delete IAM role
            try:
                role_name = f"weave-lambda-{deployment_name}"
                # Detach policies
                self._iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                )
                # Delete role
                self._iam_client.delete_role(RoleName=role_name)
            except Exception as e:
                self.log(f"Could not delete IAM role: {e}", "yellow")

            return True

        except self._client_error as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return True  # Already deleted
            raise

    def list_deployments(self) -> List[DeploymentInfo]:
        """List all Lambda deployments.

        Returns:
            List of deployment information
        """
        # Initialize clients
        credentials = self.auth_manager.get_credentials(provider_name="aws")
        self._init_clients(credentials)

        deployments = []

        try:
            # List Lambda functions with weave prefix
            response = self._lambda_client.list_functions()

            for function in response.get("Functions", []):
                # Only include Weave deployments (based on tags or name pattern)
                if "weave" in function["FunctionName"].lower():
                    deployments.append(
                        DeploymentInfo(
                            name=function["FunctionName"],
                            provider="aws",
                            status=DeploymentStatus.ACTIVE,
                            region=credentials["region"],
                            metadata={
                                "function_arn": function["FunctionArn"],
                                "runtime": function["Runtime"],
                                "last_modified": function["LastModified"],
                            },
                        )
                    )

        except Exception as e:
            self.log(f"Error listing deployments: {e}", "yellow")

        return deployments
