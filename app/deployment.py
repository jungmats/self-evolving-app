"""Deployment component for controlled deployment with rollback capability."""

import os
import shutil
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import Deployment, get_db


@dataclass
class ReleaseInfo:
    """Information about a deployment release."""
    git_sha: str
    release_path: str
    timestamp: datetime
    artifacts: List[str]


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    release_path: str
    previous_release: Optional[str]
    deployment_time: float
    health_check_result: Dict[str, Any]


@dataclass
class HealthStatus:
    """Health check status information."""
    healthy: bool
    checks: Dict[str, Any]
    timestamp: datetime


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    rolled_back_to: str
    rollback_time: float


class DeploymentComponent:
    """
    Deployment component that manages versioned releases with atomic symlink switching.
    
    This component implements:
    - Versioned release directory management
    - Atomic symlink switching with rollback
    - Health checks and deployment validation (no DB migrations)
    
    Requirements: 11.3, 11.4, 11.5
    """
    
    def __init__(self, base_path: str = "/srv/app"):
        """
        Initialize deployment component.
        
        Args:
            base_path: Base directory for deployments (default: /srv/app)
        """
        self.base_path = Path(base_path)
        self.releases_path = self.base_path / "releases"
        self.current_symlink = self.base_path / "current"
        
        # Create directories if they don't exist
        self.releases_path.mkdir(parents=True, exist_ok=True)
    
    def create_release(self, git_sha: str) -> ReleaseInfo:
        """
        Create a versioned release directory using the git SHA.
        
        Args:
            git_sha: Git commit SHA for this release
            
        Returns:
            ReleaseInfo: Information about the created release
            
        Raises:
            ValueError: If git_sha is invalid
            OSError: If release directory creation fails
        """
        if not git_sha or len(git_sha) < 7:
            raise ValueError("Invalid git SHA provided")
        
        release_path = self.releases_path / git_sha
        
        # Fail fast if release already exists
        if release_path.exists():
            raise ValueError(f"Release {git_sha} already exists at {release_path}")
        
        try:
            # Create release directory
            release_path.mkdir(parents=True)
            
            # Copy current codebase to release directory
            # In a real deployment, this would copy from a build artifact or git checkout
            current_dir = Path.cwd()
            artifacts = []
            
            # Copy essential application files
            for item in ["app", "requirements.txt", "run_server.py"]:
                src = current_dir / item
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, release_path / item)
                    else:
                        shutil.copy2(src, release_path / item)
                    artifacts.append(item)
            
            return ReleaseInfo(
                git_sha=git_sha,
                release_path=str(release_path),
                timestamp=datetime.utcnow(),
                artifacts=artifacts
            )
            
        except Exception as e:
            # Clean up on failure
            if release_path.exists():
                shutil.rmtree(release_path)
            raise OSError(f"Failed to create release {git_sha}: {e}")
    
    def deploy_release(self, release_info: ReleaseInfo) -> DeploymentResult:
        """
        Deploy a release with atomic symlink switching and health checks.
        
        Args:
            release_info: Information about the release to deploy
            
        Returns:
            DeploymentResult: Result of the deployment operation
        """
        start_time = time.time()
        release_path = Path(release_info.release_path)
        
        # Validate release exists
        if not release_path.exists():
            raise ValueError(f"Release path does not exist: {release_path}")
        
        # Get previous release for rollback capability
        previous_release = None
        if self.current_symlink.exists() and self.current_symlink.is_symlink():
            previous_release = str(self.current_symlink.readlink())
        
        try:
            # Install dependencies in release directory
            self._install_dependencies(release_path)
            
            # Run health checks before switching
            health_result = self.health_check(release_path)
            if not health_result.healthy:
                raise RuntimeError(f"Health checks failed: {health_result.checks}")
            
            # Atomic symlink switch
            self._atomic_symlink_switch(release_path)
            
            # Final health check after switch
            final_health = self.health_check()
            
            deployment_time = time.time() - start_time
            
            return DeploymentResult(
                success=True,
                release_path=str(release_path),
                previous_release=previous_release,
                deployment_time=deployment_time,
                health_check_result=final_health.checks
            )
            
        except Exception as e:
            # Rollback on failure if we have a previous release
            if previous_release:
                try:
                    self._atomic_symlink_switch(Path(previous_release))
                except Exception as rollback_error:
                    # Log rollback failure but don't mask original error
                    print(f"Rollback failed: {rollback_error}")
            
            deployment_time = time.time() - start_time
            
            return DeploymentResult(
                success=False,
                release_path=str(release_path),
                previous_release=previous_release,
                deployment_time=deployment_time,
                health_check_result={"error": str(e)}
            )
    
    def rollback_release(self, previous_release: str) -> RollbackResult:
        """
        Rollback to a previous release.
        
        Args:
            previous_release: Path to the previous release to rollback to
            
        Returns:
            RollbackResult: Result of the rollback operation
        """
        start_time = time.time()
        previous_path = Path(previous_release)
        
        if not previous_path.exists():
            raise ValueError(f"Previous release does not exist: {previous_path}")
        
        try:
            # Atomic symlink switch to previous release
            self._atomic_symlink_switch(previous_path)
            
            # Verify health after rollback
            health_result = self.health_check()
            if not health_result.healthy:
                raise RuntimeError(f"Health checks failed after rollback: {health_result.checks}")
            
            rollback_time = time.time() - start_time
            
            return RollbackResult(
                success=True,
                rolled_back_to=str(previous_path),
                rollback_time=rollback_time
            )
            
        except Exception as e:
            rollback_time = time.time() - start_time
            return RollbackResult(
                success=False,
                rolled_back_to=str(previous_path),
                rollback_time=rollback_time
            )
    
    def health_check(self, release_path: Optional[Path] = None) -> HealthStatus:
        """
        Perform health checks on the deployment.
        
        Args:
            release_path: Optional path to check specific release, defaults to current
            
        Returns:
            HealthStatus: Health check results
        """
        checks = {}
        healthy = True
        
        # Determine path to check
        check_path = release_path or self.current_symlink
        
        try:
            # Check if path exists and is accessible
            checks["path_exists"] = check_path.exists()
            if not checks["path_exists"]:
                healthy = False
            
            # Check if required files exist
            if check_path.exists():
                required_files = ["app", "requirements.txt", "run_server.py"]
                for file in required_files:
                    file_path = check_path / file
                    checks[f"file_{file}"] = file_path.exists()
                    if not checks[f"file_{file}"]:
                        healthy = False
            
            # Check if we can import the main app module
            if check_path.exists():
                try:
                    # Simple import test (would be more sophisticated in production)
                    app_path = check_path / "app"
                    checks["app_importable"] = app_path.exists() and (app_path / "__init__.py").exists()
                except Exception as e:
                    checks["app_importable"] = False
                    checks["import_error"] = str(e)
                    healthy = False
            
            # Additional health checks could include:
            # - Database connectivity
            # - External service availability
            # - Configuration validation
            
        except Exception as e:
            healthy = False
            checks["health_check_error"] = str(e)
        
        return HealthStatus(
            healthy=healthy,
            checks=checks,
            timestamp=datetime.utcnow()
        )
    
    def _install_dependencies(self, release_path: Path) -> None:
        """
        Install Python dependencies for the release.
        
        Args:
            release_path: Path to the release directory
        """
        requirements_file = release_path / "requirements.txt"
        if not requirements_file.exists():
            raise FileNotFoundError(f"requirements.txt not found in {release_path}")
        
        try:
            # Install dependencies in release directory
            # In production, this might use a virtual environment
            subprocess.run([
                "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install dependencies: {e.stderr}")
    
    def _atomic_symlink_switch(self, target_path: Path) -> None:
        """
        Atomically switch the current symlink to point to the target path.
        
        Args:
            target_path: Path to switch the symlink to
        """
        if not target_path.exists():
            raise ValueError(f"Target path does not exist: {target_path}")
        
        # Create temporary symlink
        temp_symlink = self.current_symlink.with_suffix(".tmp")
        
        try:
            # Remove temp symlink if it exists
            if temp_symlink.exists():
                temp_symlink.unlink()
            
            # Create new symlink to target
            temp_symlink.symlink_to(target_path)
            
            # Atomic move (rename) to replace current symlink
            temp_symlink.replace(self.current_symlink)
            
        except Exception as e:
            # Clean up temp symlink on failure
            if temp_symlink.exists():
                temp_symlink.unlink()
            raise RuntimeError(f"Failed to switch symlink: {e}")
    
    def get_current_release(self) -> Optional[str]:
        """
        Get the currently deployed release SHA.
        
        Returns:
            Current release SHA or None if no deployment exists
        """
        if not self.current_symlink.exists() or not self.current_symlink.is_symlink():
            return None
        
        try:
            current_path = self.current_symlink.readlink()
            return current_path.name  # Return just the SHA (directory name)
        except Exception:
            return None
    
    def list_releases(self) -> List[str]:
        """
        List all available releases.
        
        Returns:
            List of release SHAs
        """
        if not self.releases_path.exists():
            return []
        
        return [d.name for d in self.releases_path.iterdir() if d.is_dir()]
    
    def record_deployment(self, db: Session, deployment_result: DeploymentResult, git_sha: str) -> Deployment:
        """
        Record deployment result in the database.
        
        Args:
            db: Database session
            deployment_result: Result of the deployment
            git_sha: Git SHA that was deployed
            
        Returns:
            Deployment record
        """
        deployment = Deployment(
            git_sha=git_sha,
            release_path=deployment_result.release_path,
            status="success" if deployment_result.success else "failed",
            deployment_time=int(deployment_result.deployment_time),
            health_check_result=json.dumps(deployment_result.health_check_result)
        )
        
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        
        return deployment