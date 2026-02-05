#!/usr/bin/env python3
"""
Deployment executor script for GitHub Actions workflow.

This script uses the DeploymentComponent to perform controlled deployments
with atomic symlink switching and rollback capability.
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.deployment import DeploymentComponent
from app.database import get_db, create_tables


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main deployment executor function."""
    parser = argparse.ArgumentParser(description='Execute deployment with rollback capability')
    parser.add_argument('action', choices=['deploy', 'rollback', 'health-check'], 
                       help='Deployment action to perform')
    parser.add_argument('--git-sha', required=False, 
                       help='Git SHA to deploy (required for deploy action)')
    parser.add_argument('--previous-release', required=False,
                       help='Previous release path for rollback (required for rollback action)')
    parser.add_argument('--base-path', required=False,
                       help='Base deployment path (overrides DEPLOYMENT_BASE_PATH env var)')
    parser.add_argument('--output-file', 
                       help='File to write deployment result JSON')
    
    args = parser.parse_args()
    
    # Determine base path from environment variable or argument
    base_path = args.base_path or os.getenv('DEPLOYMENT_BASE_PATH')
    if not base_path:
        logger.error("❌ DEPLOYMENT_BASE_PATH environment variable not set and --base-path not provided")
        logger.error("   Set DEPLOYMENT_BASE_PATH environment variable or use --base-path argument")
        sys.exit(1)
    
    logger.info(f"🚀 Starting deployment action: {args.action}")
    logger.info(f"📁 Target deployment directory: {base_path}")
    
    # Validate base path exists (fail fast)
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        logger.error(f"❌ Deployment base directory does not exist: {base_path}")
        logger.error(f"   Please create the directory first: mkdir -p {base_path}")
        sys.exit(1)
    
    if not base_path_obj.is_dir():
        logger.error(f"❌ Deployment base path is not a directory: {base_path}")
        sys.exit(1)
    
    # Check write permissions
    if not os.access(base_path, os.W_OK):
        logger.error(f"❌ No write permission to deployment directory: {base_path}")
        logger.error(f"   Check directory permissions: ls -la {base_path}")
        sys.exit(1)
    
    logger.info(f"✅ Deployment directory validated: {base_path}")
    
    # Initialize deployment component
    try:
        deployment_component = DeploymentComponent(base_path)
        logger.info("✅ DeploymentComponent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize DeploymentComponent: {e}")
        sys.exit(1)
    
    # Ensure database tables exist
    try:
        create_tables()
        logger.info("✅ Database tables verified/created")
    except Exception as e:
        logger.warning(f"⚠️  Database table creation failed: {e}")
    
    try:
        if args.action == 'deploy':
            if not args.git_sha:
                logger.error("❌ --git-sha is required for deploy action")
                sys.exit(1)
            
            result = execute_deployment(deployment_component, args.git_sha)
            
        elif args.action == 'rollback':
            if not args.previous_release:
                logger.error("❌ --previous-release is required for rollback action")
                sys.exit(1)
            
            result = execute_rollback(deployment_component, args.previous_release)
            
        elif args.action == 'health-check':
            result = execute_health_check(deployment_component)
        
        # Output result
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"📄 Result written to: {args.output_file}")
        else:
            print(json.dumps(result, indent=2, default=str))
        
        # Log final status
        if result.get('success', False):
            logger.info(f"✅ {args.action.title()} completed successfully")
        else:
            logger.error(f"❌ {args.action.title()} failed")
        
        # Exit with appropriate code
        sys.exit(0 if result.get('success', False) else 1)
        
    except Exception as e:
        logger.error(f"❌ Deployment failed with exception: {e}")
        error_result = {
            'success': False,
            'error': str(e),
            'action': args.action,
            'base_path': base_path
        }
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(error_result, f, indent=2, default=str)
        else:
            print(json.dumps(error_result, indent=2, default=str))
        
        sys.exit(1)


def execute_deployment(deployment_component: DeploymentComponent, git_sha: str) -> dict:
    """
    Execute deployment for the given git SHA.
    
    Args:
        deployment_component: Deployment component instance
        git_sha: Git SHA to deploy
        
    Returns:
        Dictionary with deployment result
    """
    logger.info(f"🚀 Starting deployment for git SHA: {git_sha}")
    
    # Create release
    logger.info("📦 Creating release directory...")
    try:
        release_info = deployment_component.create_release(git_sha)
        logger.info(f"✅ Release created successfully")
        logger.info(f"   📁 Release path: {release_info.release_path}")
        logger.info(f"   📋 Artifacts: {', '.join(release_info.artifacts)}")
    except Exception as e:
        logger.error(f"❌ Failed to create release: {e}")
        raise
    
    # Deploy release
    logger.info("🔄 Deploying release...")
    try:
        deployment_result = deployment_component.deploy_release(release_info)
    except Exception as e:
        logger.error(f"❌ Deployment failed during execution: {e}")
        raise
    
    # Record deployment in database
    try:
        db_gen = get_db()
        db = next(db_gen)
        deployment_record = deployment_component.record_deployment(db, deployment_result, git_sha)
        logger.info(f"📊 Deployment recorded in database with ID: {deployment_record.id}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to record deployment in database: {e}")
    finally:
        try:
            db.close()
        except:
            pass
    
    if deployment_result.success:
        logger.info(f"✅ Deployment successful!")
        logger.info(f"   🎯 Deployed to: {deployment_result.release_path}")
        logger.info(f"   ⏱️  Deployment time: {deployment_result.deployment_time:.2f} seconds")
        logger.info(f"   🔗 Current symlink updated")
        if deployment_result.previous_release:
            logger.info(f"   📋 Previous release: {deployment_result.previous_release}")
    else:
        logger.error(f"❌ Deployment failed!")
        logger.error(f"   🔍 Health check results: {deployment_result.health_check_result}")
        if deployment_result.previous_release:
            logger.info(f"   🔄 System rolled back to: {deployment_result.previous_release}")
    
    return {
        'success': deployment_result.success,
        'action': 'deploy',
        'git_sha': git_sha,
        'release_path': deployment_result.release_path,
        'previous_release': deployment_result.previous_release,
        'deployment_time': deployment_result.deployment_time,
        'health_check_result': deployment_result.health_check_result
    }


def execute_rollback(deployment_component: DeploymentComponent, previous_release: str) -> dict:
    """
    Execute rollback to previous release.
    
    Args:
        deployment_component: Deployment component instance
        previous_release: Path to previous release
        
    Returns:
        Dictionary with rollback result
    """
    logger.info(f"🔄 Starting rollback to: {previous_release}")
    
    try:
        rollback_result = deployment_component.rollback_release(previous_release)
    except Exception as e:
        logger.error(f"❌ Rollback failed during execution: {e}")
        raise
    
    if rollback_result.success:
        logger.info(f"✅ Rollback successful!")
        logger.info(f"   🎯 Rolled back to: {rollback_result.rolled_back_to}")
        logger.info(f"   ⏱️  Rollback time: {rollback_result.rollback_time:.2f} seconds")
        logger.info(f"   🔗 Current symlink restored")
    else:
        logger.error(f"❌ Rollback failed!")
        logger.error(f"   🎯 Target release: {previous_release}")
    
    return {
        'success': rollback_result.success,
        'action': 'rollback',
        'rolled_back_to': rollback_result.rolled_back_to,
        'rollback_time': rollback_result.rollback_time
    }


def execute_health_check(deployment_component: DeploymentComponent) -> dict:
    """
    Execute health check on current deployment.
    
    Args:
        deployment_component: Deployment component instance
        
    Returns:
        Dictionary with health check result
    """
    logger.info("🏥 Performing health check...")
    
    try:
        health_result = deployment_component.health_check()
        current_release = deployment_component.get_current_release()
    except Exception as e:
        logger.error(f"❌ Health check failed with exception: {e}")
        raise
    
    if health_result.healthy:
        logger.info("✅ Health check passed!")
        logger.info(f"   🎯 Current release: {current_release or 'None'}")
        logger.info(f"   ✅ All health checks: {health_result.checks}")
    else:
        logger.error("❌ Health check failed!")
        logger.error(f"   🎯 Current release: {current_release or 'None'}")
        logger.error(f"   ❌ Failed checks: {health_result.checks}")
    
    return {
        'success': health_result.healthy,
        'action': 'health-check',
        'current_release': current_release,
        'health_checks': health_result.checks,
        'timestamp': health_result.timestamp
    }


if __name__ == '__main__':
    main()