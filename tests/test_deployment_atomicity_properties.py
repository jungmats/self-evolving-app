"""Property-based tests for deployment atomicity and rollback."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

from app.deployment import DeploymentComponent, ReleaseInfo, DeploymentResult, HealthStatus


class TestDeploymentAtomicityProperties:
    """Property tests for deployment atomicity and rollback capabilities."""

    def setup_method(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        self.deployment_component = DeploymentComponent(str(self.base_path))
        
        # Create a mock application structure
        self.mock_app_dir = Path(tempfile.mkdtemp())
        (self.mock_app_dir / "app").mkdir()
        (self.mock_app_dir / "app" / "__init__.py").touch()
        (self.mock_app_dir / "requirements.txt").write_text("fastapi==0.104.1\n")
        (self.mock_app_dir / "run_server.py").write_text("# Mock server\n")

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.mock_app_dir, ignore_errors=True)

    @given(
        base_sha=st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
        deployment_count=st.integers(min_value=1, max_value=5)
    )
    def test_deployment_creates_versioned_release_directory(self, base_sha, deployment_count):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any deployment execution, the deployment should create a versioned release 
        directory using the git SHA.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Assume valid git SHA format
        assume(base_sha.isalnum())
        
        with patch.object(self.deployment_component, '_install_dependencies'):
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                mock_health.return_value = HealthStatus(
                    healthy=True,
                    checks={"path_exists": True},
                    timestamp=datetime.utcnow()
                )
                
                # Create multiple deployments to test versioning with guaranteed unique SHAs
                created_releases = []
                for i in range(deployment_count):
                    # Ensure unique SHA by combining base with counter and timestamp
                    unique_sha = f"{base_sha}{i:02d}{int(datetime.utcnow().timestamp() * 1000000) % 1000000:06d}"
                    
                    # Create release
                    release_info = self.deployment_component.create_release(unique_sha)
                    created_releases.append(release_info)
                    
                    # Verify release directory was created with correct name
                    release_path = Path(release_info.release_path)
                    assert release_path.exists()
                    assert release_path.name == unique_sha
                    assert release_path.parent == self.deployment_component.releases_path
                
                # Verify all releases exist and are uniquely versioned
                assert len(created_releases) == deployment_count
                release_names = [Path(r.release_path).name for r in created_releases]
                assert len(set(release_names)) == deployment_count  # All unique

    @given(
        base_sha=st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
        should_fail_health_check=st.booleans()
    )
    def test_deployment_atomic_symlink_switching(self, base_sha, should_fail_health_check):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any deployment execution, the deployment should atomically switch the 
        current symlink and automatically rollback on failure.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Assume valid git SHA format
        assume(base_sha.isalnum())
        
        # Create unique SHAs with timestamp to avoid collisions
        timestamp = int(datetime.utcnow().timestamp() * 1000000) % 1000000
        initial_sha = f"init{base_sha[:8]}{timestamp:06d}"
        new_sha = f"new{base_sha[:8]}{timestamp:06d}"
        
        with patch.object(self.deployment_component, '_install_dependencies'):
            # Create initial release and deploy it
            initial_release = self.deployment_component.create_release(initial_sha)
            
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                mock_health.return_value = HealthStatus(
                    healthy=True,
                    checks={"path_exists": True},
                    timestamp=datetime.utcnow()
                )
                
                initial_result = self.deployment_component.deploy_release(initial_release)
                assert initial_result.success
                
                # Verify initial symlink points to initial release
                assert self.deployment_component.current_symlink.exists()
                assert self.deployment_component.current_symlink.is_symlink()
                current_target = self.deployment_component.current_symlink.readlink()
                assert current_target.name == initial_sha
            
            # Create new release
            new_release = self.deployment_component.create_release(new_sha)
            
            # Configure health check to fail or succeed based on test parameter
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                if should_fail_health_check:
                    # First call (pre-deployment check) fails
                    mock_health.return_value = HealthStatus(
                        healthy=False,
                        checks={"path_exists": False},
                        timestamp=datetime.utcnow()
                    )
                    
                    # Deploy should fail and rollback
                    new_result = self.deployment_component.deploy_release(new_release)
                    assert not new_result.success
                    
                    # Verify symlink still points to initial release (rollback occurred)
                    current_target = self.deployment_component.current_symlink.readlink()
                    assert current_target.name == initial_sha
                    
                else:
                    # Health checks succeed
                    mock_health.return_value = HealthStatus(
                        healthy=True,
                        checks={"path_exists": True},
                        timestamp=datetime.utcnow()
                    )
                    
                    # Deploy should succeed
                    new_result = self.deployment_component.deploy_release(new_release)
                    assert new_result.success
                    
                    # Verify symlink now points to new release
                    current_target = self.deployment_component.current_symlink.readlink()
                    assert current_target.name == new_sha

    @given(
        base_shas=st.lists(
            st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    def test_rollback_restores_previous_release(self, base_shas):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any rollback operation, the system should atomically switch back to the 
        previous release and verify health.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Filter valid git SHAs and ensure uniqueness with timestamp
        timestamp = int(datetime.utcnow().timestamp() * 1000000) % 1000000
        valid_shas = [f"{sha}{i:02d}{timestamp:06d}" for i, sha in enumerate(base_shas) if sha.isalnum()]
        assume(len(valid_shas) >= 2)
        
        with patch.object(self.deployment_component, '_install_dependencies'):
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                mock_health.return_value = HealthStatus(
                    healthy=True,
                    checks={"path_exists": True},
                    timestamp=datetime.utcnow()
                )
                
                # Deploy multiple releases in sequence
                deployed_releases = []
                for sha in valid_shas:
                    release_info = self.deployment_component.create_release(sha)
                    result = self.deployment_component.deploy_release(release_info)
                    assert result.success
                    deployed_releases.append((sha, release_info, result))
                
                # Current deployment should be the last one
                current_sha = valid_shas[-1]
                current_target = self.deployment_component.current_symlink.readlink()
                assert current_target.name == current_sha
                
                # Rollback to previous release
                previous_sha = valid_shas[-2]
                previous_release_path = str(self.deployment_component.releases_path / previous_sha)
                
                rollback_result = self.deployment_component.rollback_release(previous_release_path)
                assert rollback_result.success
                assert rollback_result.rolled_back_to == previous_release_path
                
                # Verify symlink now points to previous release
                current_target = self.deployment_component.current_symlink.readlink()
                assert current_target.name == previous_sha

    @given(
        base_sha=st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
        health_check_components=st.lists(
            st.sampled_from(["path_exists", "file_app", "file_requirements.txt", "file_run_server.py", "app_importable"]),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    def test_health_checks_validate_deployment_integrity(self, base_sha, health_check_components):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any deployment, health checks should validate deployment integrity and 
        prevent deployment of unhealthy releases.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Assume valid git SHA format and create unique SHA
        assume(base_sha.isalnum())
        timestamp = int(datetime.utcnow().timestamp() * 1000000) % 1000000
        git_sha = f"{base_sha}{timestamp:06d}"
        
        with patch.object(self.deployment_component, '_install_dependencies'):
            # Create release
            release_info = self.deployment_component.create_release(git_sha)
            release_path = Path(release_info.release_path)
            
            # Simulate health check failures by removing required components
            if "file_app" in health_check_components:
                app_dir = release_path / "app"
                if app_dir.exists():
                    shutil.rmtree(app_dir)
            
            if "file_requirements.txt" in health_check_components:
                req_file = release_path / "requirements.txt"
                if req_file.exists():
                    req_file.unlink()
            
            if "file_run_server.py" in health_check_components:
                server_file = release_path / "run_server.py"
                if server_file.exists():
                    server_file.unlink()
            
            # Perform health check
            health_result = self.deployment_component.health_check(release_path)
            
            # Verify health check detects missing components
            for component in health_check_components:
                if component.startswith("file_"):
                    file_name = component.replace("file_", "")
                    assert component in health_result.checks
                    # If we removed the file, health check should detect it
                    if component in ["file_app", "file_requirements.txt", "file_run_server.py"]:
                        assert not health_result.checks[component]
            
            # Overall health should be false if any required component is missing
            required_components = ["file_app", "file_requirements.txt", "file_run_server.py"]
            missing_required = any(comp in health_check_components for comp in required_components)
            
            if missing_required:
                assert not health_result.healthy
            else:
                # If no required components are missing, health should be true
                assert health_result.healthy

    @given(
        base_sha=st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
        simulate_failure=st.booleans()
    )
    def test_deployment_failure_preserves_system_state(self, base_sha, simulate_failure):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any deployment failure, the system should preserve the previous state 
        and not leave the system in an inconsistent state.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Assume valid git SHA format and create unique SHAs
        assume(base_sha.isalnum())
        timestamp = int(datetime.utcnow().timestamp() * 1000000) % 1000000
        initial_sha = f"stable{base_sha[:8]}{timestamp:06d}"
        new_sha = f"test{base_sha[:8]}{timestamp:06d}"
        
        # Create and deploy initial release
        with patch.object(self.deployment_component, '_install_dependencies'):
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                mock_health.return_value = HealthStatus(
                    healthy=True,
                    checks={"path_exists": True},
                    timestamp=datetime.utcnow()
                )
                
                initial_release = self.deployment_component.create_release(initial_sha)
                initial_result = self.deployment_component.deploy_release(initial_release)
                assert initial_result.success
                
                # Record initial state
                initial_target = self.deployment_component.current_symlink.readlink()
                assert initial_target.name == initial_sha
            
            # Attempt new deployment that may fail
            new_release = self.deployment_component.create_release(new_sha)
            
            if simulate_failure:
                # Simulate deployment failure (e.g., dependency installation failure)
                with patch.object(self.deployment_component, '_install_dependencies') as mock_install:
                    mock_install.side_effect = RuntimeError("Dependency installation failed")
                    
                    with patch.object(self.deployment_component, 'health_check') as mock_health:
                        mock_health.return_value = HealthStatus(
                            healthy=True,
                            checks={"path_exists": True},
                            timestamp=datetime.utcnow()
                        )
                        
                        # Deploy should fail
                        new_result = self.deployment_component.deploy_release(new_release)
                        assert not new_result.success
                
                # Verify system state is preserved (still points to initial release)
                current_target = self.deployment_component.current_symlink.readlink()
                assert current_target.name == initial_sha
                
                # Verify system is still functional (health check passes)
                health_result = self.deployment_component.health_check()
                assert health_result.healthy
            
            else:
                # Normal successful deployment
                with patch.object(self.deployment_component, 'health_check') as mock_health:
                    mock_health.return_value = HealthStatus(
                        healthy=True,
                        checks={"path_exists": True},
                        timestamp=datetime.utcnow()
                    )
                    
                    new_result = self.deployment_component.deploy_release(new_release)
                    assert new_result.success
                    
                    # Verify system state updated to new release
                    current_target = self.deployment_component.current_symlink.readlink()
                    assert current_target.name == new_sha

    def test_deployment_component_interface_completeness(self):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        Verify that the deployment component implements all required interfaces
        as specified in the design document.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Verify all required methods exist
        required_methods = [
            'create_release',
            'deploy_release', 
            'rollback_release',
            'health_check',
            'get_current_release',
            'list_releases',
            'record_deployment'
        ]
        
        for method_name in required_methods:
            assert hasattr(self.deployment_component, method_name), f"Missing required method: {method_name}"
            assert callable(getattr(self.deployment_component, method_name)), f"Method {method_name} is not callable"
        
        # Verify required attributes exist
        required_attributes = ['base_path', 'releases_path', 'current_symlink']
        for attr_name in required_attributes:
            assert hasattr(self.deployment_component, attr_name), f"Missing required attribute: {attr_name}"

    @given(
        base_sha=st.text(min_size=4, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd")))
    )
    def test_deployment_timing_and_metrics_collection(self, base_sha):
        """
        Feature: self-evolving-app, Property 11: Deployment Atomicity and Rollback
        
        For any deployment operation, timing metrics should be collected and 
        included in the deployment result.
        **Validates: Requirements 11.3, 11.4, 11.5**
        """
        # Assume valid git SHA format and create unique SHA
        assume(base_sha.isalnum())
        timestamp = int(datetime.utcnow().timestamp() * 1000000) % 1000000
        git_sha = f"{base_sha}{timestamp:06d}"
        
        with patch.object(self.deployment_component, '_install_dependencies'):
            with patch.object(self.deployment_component, 'health_check') as mock_health:
                mock_health.return_value = HealthStatus(
                    healthy=True,
                    checks={"path_exists": True},
                    timestamp=datetime.utcnow()
                )
                
                # Create and deploy release
                release_info = self.deployment_component.create_release(git_sha)
                result = self.deployment_component.deploy_release(release_info)
                
                # Verify timing metrics are collected
                assert hasattr(result, 'deployment_time')
                assert isinstance(result.deployment_time, (int, float))
                assert result.deployment_time >= 0
                
                # Verify health check results are included
                assert hasattr(result, 'health_check_result')
                assert isinstance(result.health_check_result, dict)