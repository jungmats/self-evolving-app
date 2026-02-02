"""Claude client factory for the Self-Evolving Web Application.

This module provides a factory for creating Claude clients, supporting both
API-based and CLI-based implementations with seamless switching.
"""

import os
import logging
from typing import Optional, Union, Protocol
from enum import Enum

from claude_client import ClaudeClient, ClaudeClientError
from claude_cli_client import ClaudeCLIClient, ClaudeCLIError

logger = logging.getLogger(__name__)


class ClientType(Enum):
    """Supported Claude client types."""
    API = "api"
    CLI = "cli"


class ClaudeClientProtocol(Protocol):
    """Protocol defining the interface for Claude clients."""
    
    def triage_analysis(self, constrained_prompt: str, trace_id: str) -> dict:
        """Perform triage analysis."""
        ...
    
    def planning_analysis(self, constrained_prompt: str, trace_id: str) -> dict:
        """Perform planning analysis."""
        ...
    
    def prioritization_analysis(self, constrained_prompt: str, trace_id: str) -> dict:
        """Perform prioritization analysis."""
        ...
    
    def implementation_generation(self, constrained_prompt: str, trace_id: str) -> dict:
        """Generate implementation."""
        ...


class ClaudeClientFactory:
    """
    Factory for creating Claude clients with automatic fallback support.
    
    Supports both API-based and CLI-based clients with configuration-driven
    selection and automatic fallback capabilities.
    """
    
    def __init__(self):
        """Initialize the factory."""
        self._preferred_client_type = self._determine_preferred_client_type()
        self._repository_root = os.getenv("REPO_ROOT", os.getcwd())
    
    def _determine_preferred_client_type(self) -> ClientType:
        """Determine the preferred client type based on environment."""
        # Check environment variable for explicit preference
        client_type_env = os.getenv("CLAUDE_CLIENT_TYPE", "").lower()
        
        if client_type_env == "cli":
            return ClientType.CLI
        elif client_type_env == "api":
            return ClientType.API
        
        # Auto-detect based on environment
        # Prefer CLI if we're in a GitHub Actions environment with repository context
        if os.getenv("GITHUB_ACTIONS") and os.getenv("GITHUB_WORKSPACE"):
            logger.info("GitHub Actions environment detected, preferring Claude CLI")
            return ClientType.CLI
        
        # Prefer CLI if Claude CLI is available and we have repository context
        try:
            import subprocess
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("Claude CLI available, preferring CLI client")
                return ClientType.CLI
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        
        # Default to CLI client (preferred)
        logger.info("Defaulting to Claude CLI client")
        return ClientType.CLI
    
    def create_client(
        self,
        client_type: Optional[ClientType] = None,
        fallback_enabled: bool = True
    ) -> ClaudeClientProtocol:
        """
        Create a Claude client instance.
        
        Args:
            client_type: Specific client type to create (defaults to auto-detection)
            fallback_enabled: Whether to enable fallback to alternative client
            
        Returns:
            Configured Claude client instance
            
        Raises:
            ClaudeClientError: If client creation fails and no fallback is available
        """
        target_type = client_type or self._preferred_client_type
        
        try:
            if target_type == ClientType.CLI:
                return self._create_cli_client()
            else:
                return self._create_api_client()
                
        except (ClaudeClientError, ClaudeCLIError) as e:
            if not fallback_enabled:
                raise
            
            logger.warning(f"Failed to create {target_type.value} client: {e}")
            
            # Try fallback client
            fallback_type = ClientType.API if target_type == ClientType.CLI else ClientType.CLI
            logger.info(f"Attempting fallback to {fallback_type.value} client")
            
            try:
                if fallback_type == ClientType.CLI:
                    return self._create_cli_client()
                else:
                    return self._create_api_client()
            except (ClaudeClientError, ClaudeCLIError) as fallback_error:
                raise ClaudeClientError(
                    f"Both {target_type.value} and {fallback_type.value} clients failed. "
                    f"Primary error: {e}. Fallback error: {fallback_error}"
                )
    
    def _create_api_client(self) -> ClaudeClient:
        """Create API-based Claude client."""
        try:
            return ClaudeClient()
        except Exception as e:
            raise ClaudeClientError(f"Failed to create API client: {e}")
    
    def _create_cli_client(self) -> ClaudeCLIClient:
        """Create CLI-based Claude client."""
        try:
            return ClaudeCLIClient(repository_root=self._repository_root)
        except Exception as e:
            raise ClaudeCLIError(f"Failed to create CLI client: {e}")
    
    def get_available_client_types(self) -> list[ClientType]:
        """
        Get list of available client types.
        
        Returns:
            List of client types that can be successfully created
        """
        available_types = []
        
        # Test API client
        try:
            self._create_api_client()
            available_types.append(ClientType.API)
        except Exception:
            pass
        
        # Test CLI client
        try:
            self._create_cli_client()
            available_types.append(ClientType.CLI)
        except Exception:
            pass
        
        return available_types
    
    def get_client_info(self, client_type: ClientType) -> dict:
        """
        Get information about a specific client type.
        
        Args:
            client_type: Client type to get information about
            
        Returns:
            Dictionary with client information
        """
        if client_type == ClientType.API:
            return {
                "type": "api",
                "name": "Claude API Client (DEPRECATED)",
                "description": "Legacy API integration - use Claude CLI instead",
                "features": [
                    "Direct API access (deprecated)",
                    "Structured response parsing",
                    "Rate limiting support",
                    "Authentication handling"
                ],
                "requirements": [
                    "DEPRECATED - Use Claude CLI instead"
                ]
            }
        elif client_type == ClientType.CLI:
            return {
                "type": "cli",
                "name": "Claude CLI Client",
                "description": "CLI-based integration with full repository context",
                "features": [
                    "Full repository context",
                    "Code-aware analysis",
                    "File relationship understanding",
                    "Architectural pattern recognition",
                    "Enhanced implementation suggestions"
                ],
                "requirements": [
                    "Claude CLI installed and authenticated",
                    "Repository access",
                    "Local file system access"
                ]
            }
        else:
            return {"type": "unknown", "error": "Unknown client type"}


# Global factory instance
_factory = ClaudeClientFactory()


def get_claude_client(
    client_type: Optional[ClientType] = None,
    fallback_enabled: bool = True
) -> ClaudeClientProtocol:
    """
    Get a configured Claude client instance.
    
    This is the main entry point for obtaining Claude clients throughout
    the application. It handles client type selection, creation, and fallback.
    
    Args:
        client_type: Specific client type to create (defaults to auto-detection)
        fallback_enabled: Whether to enable fallback to alternative client
        
    Returns:
        Configured Claude client instance
        
    Raises:
        ClaudeClientError: If client creation fails and no fallback is available
    """
    return _factory.create_client(client_type=client_type, fallback_enabled=fallback_enabled)


def get_available_client_types() -> list[ClientType]:
    """
    Get list of available client types.
    
    Returns:
        List of client types that can be successfully created
    """
    return _factory.get_available_client_types()


def get_client_info(client_type: ClientType) -> dict:
    """
    Get information about a specific client type.
    
    Args:
        client_type: Client type to get information about
        
    Returns:
        Dictionary with client information
    """
    return _factory.get_client_info(client_type)


def set_preferred_client_type(client_type: ClientType) -> None:
    """
    Set the preferred client type for future client creation.
    
    Args:
        client_type: Preferred client type
    """
    global _factory
    _factory._preferred_client_type = client_type
    logger.info(f"Preferred Claude client type set to: {client_type.value}")


def get_preferred_client_type() -> ClientType:
    """
    Get the current preferred client type.
    
    Returns:
        Current preferred client type
    """
    return _factory._preferred_client_type