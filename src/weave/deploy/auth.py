"""Authentication and credential management for deployment providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, SecretStr
from enum import Enum
import os


class AuthMethod(str, Enum):
    """Supported authentication methods."""

    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    IAM_ROLE = "iam_role"
    OAUTH = "oauth"
    ENV_VARS = "env_vars"
    CONFIG_FILE = "config_file"


class AuthConfig(BaseModel):
    """Base authentication configuration."""

    method: AuthMethod = Field(..., description="Authentication method")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Method-specific configuration"
    )


class APIKeyAuth(BaseModel):
    """API key authentication."""

    api_key: SecretStr = Field(..., description="API key")
    api_secret: Optional[SecretStr] = Field(None, description="API secret")


class ServiceAccountAuth(BaseModel):
    """Service account authentication (e.g., GCP service account JSON)."""

    credentials_file: str = Field(..., description="Path to credentials file")
    project_id: Optional[str] = Field(None, description="Project ID")


class IAMRoleAuth(BaseModel):
    """IAM role-based authentication (e.g., AWS IAM)."""

    role_arn: Optional[str] = Field(None, description="IAM role ARN")
    access_key_id: Optional[SecretStr] = Field(None, description="Access key ID")
    secret_access_key: Optional[SecretStr] = Field(None, description="Secret access key")
    session_token: Optional[SecretStr] = Field(None, description="Session token")
    region: Optional[str] = Field(None, description="AWS region")


class CredentialProvider(ABC):
    """Abstract base class for credential providers.

    Credential providers resolve authentication credentials from various sources
    (environment variables, config files, credential stores, etc.)
    """

    @abstractmethod
    def get_credentials(self, config: AuthConfig) -> Dict[str, Any]:
        """Get credentials for the provider.

        Args:
            config: Authentication configuration

        Returns:
            Dictionary of credentials

        Raises:
            AuthenticationError: If credentials cannot be resolved
        """
        pass

    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials.

        Args:
            credentials: Credentials to validate

        Returns:
            True if valid

        Raises:
            AuthenticationError: If validation fails
        """
        pass


class EnvironmentCredentialProvider(CredentialProvider):
    """Resolve credentials from environment variables."""

    def __init__(self, env_mapping: Optional[Dict[str, str]] = None):
        """Initialize environment credential provider.

        Args:
            env_mapping: Mapping of credential keys to environment variable names
        """
        self.env_mapping = env_mapping or {}

    def get_credentials(self, config: AuthConfig) -> Dict[str, Any]:
        """Get credentials from environment variables.

        Args:
            config: Auth configuration with environment variable names

        Returns:
            Dictionary of credentials
        """
        credentials = {}

        for key, env_var in self.env_mapping.items():
            value = os.getenv(env_var)
            if value:
                credentials[key] = value

        return credentials

    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials are present.

        Args:
            credentials: Credentials dictionary

        Returns:
            True if all required credentials are present
        """
        return len(credentials) > 0


class FileCredentialProvider(CredentialProvider):
    """Resolve credentials from configuration files."""

    def __init__(self, file_path: Optional[str] = None):
        """Initialize file credential provider.

        Args:
            file_path: Path to credentials file
        """
        self.file_path = file_path

    def get_credentials(self, config: AuthConfig) -> Dict[str, Any]:
        """Get credentials from file.

        Args:
            config: Auth configuration

        Returns:
            Dictionary of credentials
        """
        import json
        from pathlib import Path

        file_path = self.file_path or config.config.get("credentials_file")
        if not file_path:
            return {}

        path = Path(file_path).expanduser()
        if not path.exists():
            return {}

        with open(path) as f:
            if file_path.endswith(".json"):
                return json.load(f)
            else:
                # Simple key=value format
                credentials = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            credentials[key.strip()] = value.strip()
                return credentials

    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials.

        Args:
            credentials: Credentials dictionary

        Returns:
            True if valid
        """
        return len(credentials) > 0


class AuthenticationManager:
    """Manages authentication for deployment providers.

    Supports multiple authentication methods and credential sources.
    """

    def __init__(self):
        """Initialize authentication manager."""
        self.credential_providers: Dict[str, CredentialProvider] = {
            "env": EnvironmentCredentialProvider(),
            "file": FileCredentialProvider(),
        }

    def register_provider(self, name: str, provider: CredentialProvider) -> None:
        """Register a custom credential provider.

        Args:
            name: Provider name
            provider: Credential provider instance
        """
        self.credential_providers[name] = provider

    def get_credentials(
        self, auth_config: Optional[AuthConfig] = None, provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get credentials for a deployment provider.

        Args:
            auth_config: Authentication configuration
            provider_name: Provider name for default credential resolution

        Returns:
            Dictionary of credentials

        Raises:
            AuthenticationError: If credentials cannot be resolved
        """
        from ..core.exceptions import WeaveError

        if not auth_config:
            # Try default credential resolution
            if provider_name:
                return self._get_default_credentials(provider_name)
            return {}

        # Use specified authentication method
        if auth_config.method == AuthMethod.ENV_VARS:
            provider = self.credential_providers.get("env")
            if provider:
                return provider.get_credentials(auth_config)

        elif auth_config.method == AuthMethod.CONFIG_FILE:
            provider = self.credential_providers.get("file")
            if provider:
                return provider.get_credentials(auth_config)

        elif auth_config.method == AuthMethod.API_KEY:
            return {
                "api_key": auth_config.config.get("api_key"),
                "api_secret": auth_config.config.get("api_secret"),
            }

        elif auth_config.method == AuthMethod.SERVICE_ACCOUNT:
            return {
                "credentials_file": auth_config.config.get("credentials_file"),
                "project_id": auth_config.config.get("project_id"),
            }

        elif auth_config.method == AuthMethod.IAM_ROLE:
            return {
                "role_arn": auth_config.config.get("role_arn"),
                "access_key_id": auth_config.config.get("access_key_id"),
                "secret_access_key": auth_config.config.get("secret_access_key"),
                "session_token": auth_config.config.get("session_token"),
                "region": auth_config.config.get("region"),
            }

        raise WeaveError(
            f"Unsupported authentication method: {auth_config.method}",
            suggestion="Check your authentication configuration",
        )

    def _get_default_credentials(self, provider_name: str) -> Dict[str, Any]:
        """Get default credentials for a provider.

        Args:
            provider_name: Provider name (aws, gcp, etc.)

        Returns:
            Dictionary of credentials from environment
        """
        if provider_name == "aws":
            return {
                "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "session_token": os.getenv("AWS_SESSION_TOKEN"),
                "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            }
        elif provider_name == "gcp":
            return {
                "credentials_file": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                "project_id": os.getenv("GCP_PROJECT_ID"),
            }
        elif provider_name == "docker":
            return {
                "registry_url": os.getenv("DOCKER_REGISTRY_URL"),
                "username": os.getenv("DOCKER_USERNAME"),
                "password": os.getenv("DOCKER_PASSWORD"),
            }

        return {}

    def validate_credentials(
        self, credentials: Dict[str, Any], required_keys: Optional[list] = None
    ) -> bool:
        """Validate credentials have required keys.

        Args:
            credentials: Credentials dictionary
            required_keys: List of required credential keys

        Returns:
            True if valid

        Raises:
            AuthenticationError: If validation fails
        """
        from ..core.exceptions import WeaveError

        if not credentials:
            raise WeaveError(
                "No credentials provided",
                suggestion="Set credentials in environment variables or config file",
            )

        if required_keys:
            missing = [key for key in required_keys if not credentials.get(key)]
            if missing:
                raise WeaveError(
                    f"Missing required credentials: {', '.join(missing)}",
                    suggestion="Check your authentication configuration",
                )

        return True
