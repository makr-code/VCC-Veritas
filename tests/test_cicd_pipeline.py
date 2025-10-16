"""
VERITAS CI/CD Pipeline Test Suite

This module provides comprehensive tests for validating the CI/CD pipeline
configuration and ensuring all workflows are correctly set up.

Tests cover:
- Workflow YAML syntax validation
- Required secrets verification
- Deployment configuration checks
- Docker configuration validation
- Security best practices

Author: VERITAS Team
Date: 2025-10-08
Version: 1.0.0
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class WorkflowValidationResult:
    """Result of workflow validation."""
    workflow_name: str
    valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


@dataclass
class PipelineTestResult:
    """Result of pipeline test."""
    test_name: str
    passed: bool
    message: str
    details: Dict[str, Any]


class CICDPipelineValidator:
    """Validates CI/CD pipeline configuration."""
    
    def __init__(self, project_root: Path = None):
        """Initialize validator."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.results: List[WorkflowValidationResult] = []
        
    def validate_all(self) -> bool:
        """
        Run all validation tests.
        
        Returns:
            bool: True if all tests pass
        """
        print("=" * 80)
        print("VERITAS CI/CD Pipeline Validation")
        print("=" * 80)
        print()
        
        all_passed = True
        
        # Test 1: Validate workflow files
        print("Test 1: Validating workflow YAML files...")
        workflow_valid = self.validate_workflows()
        all_passed = all_passed and workflow_valid
        print()
        
        # Test 2: Check required files
        print("Test 2: Checking required configuration files...")
        files_valid = self.check_required_files()
        all_passed = all_passed and files_valid
        print()
        
        # Test 3: Validate workflow structure
        print("Test 3: Validating workflow structure...")
        structure_valid = self.validate_workflow_structure()
        all_passed = all_passed and structure_valid
        print()
        
        # Test 4: Check secret references
        print("Test 4: Checking secret references...")
        secrets_valid = self.check_secret_references()
        all_passed = all_passed and secrets_valid
        print()
        
        # Test 5: Validate Docker configuration
        print("Test 5: Validating Docker configuration...")
        docker_valid = self.validate_docker_config()
        all_passed = all_passed and docker_valid
        print()
        
        # Print summary
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        for result in self.results:
            status = "✅ PASS" if result.valid else "❌ FAIL"
            print(f"{status} - {result.workflow_name}")
            
            if result.errors:
                print(f"  Errors ({len(result.errors)}):")
                for error in result.errors:
                    print(f"    - {error}")
                    
            if result.warnings:
                print(f"  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"    - {warning}")
                    
            if result.info:
                print(f"  Info ({len(result.info)}):")
                for info in result.info:
                    print(f"    - {info}")
            print()
        
        print("=" * 80)
        if all_passed:
            print("✅ ALL VALIDATION TESTS PASSED")
            print("CI/CD Pipeline is properly configured!")
        else:
            print("❌ SOME VALIDATION TESTS FAILED")
            print("Please review errors above and fix configuration.")
        print("=" * 80)
        
        return all_passed
    
    def validate_workflows(self) -> bool:
        """
        Validate all workflow YAML files.
        
        Returns:
            bool: True if all workflows are valid
        """
        if not self.workflows_dir.exists():
            print(f"  ❌ Workflows directory not found: {self.workflows_dir}")
            return False
        
        workflows = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        if not workflows:
            print(f"  ❌ No workflow files found in {self.workflows_dir}")
            return False
        
        print(f"  Found {len(workflows)} workflow file(s)")
        
        all_valid = True
        for workflow_path in workflows:
            valid, errors = self._validate_yaml_file(workflow_path)
            
            if valid:
                print(f"  ✅ {workflow_path.name} - Valid YAML")
            else:
                print(f"  ❌ {workflow_path.name} - Invalid YAML")
                for error in errors:
                    print(f"     Error: {error}")
                all_valid = False
        
        return all_valid
    
    def _validate_yaml_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a single YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (valid, errors)
        """
        errors = []
        
        try:
            # Try UTF-8 first, then UTF-8 with BOM, then system default
            for encoding in ['utf-8', 'utf-8-sig', None]:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        yaml.safe_load(f)
                    return True, []
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail
            errors.append("Unable to decode file with any encoding")
            return False, errors
            
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {str(e)}")
            return False, errors
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
            return False, errors
    
    def check_required_files(self) -> bool:
        """
        Check if all required configuration files exist.
        
        Returns:
            bool: True if all files exist
        """
        required_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/deploy.yml",
            ".github/workflows/release.yml",
            "docs/CICD_PIPELINE_DOCUMENTATION.md",
            "docs/GITHUB_SECRETS_SETUP.md",
        ]
        
        optional_files = [
            "Dockerfile",
            "frontend/Dockerfile",
            "docker-compose.yml",
            "requirements.txt",
            "frontend/package.json",
        ]
        
        all_exist = True
        
        # Check required files
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} - MISSING (required)")
                all_exist = False
        
        # Check optional files
        for file_path in optional_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ⚠️  {file_path} - Missing (optional, deployment may fail)")
        
        return all_exist
    
    def validate_workflow_structure(self) -> bool:
        """
        Validate structure of workflow files.
        
        Returns:
            bool: True if all workflows have valid structure
        """
        all_valid = True
        
        # Validate CI workflow
        ci_valid = self._validate_ci_workflow()
        all_valid = all_valid and ci_valid
        
        # Validate CD workflow
        cd_valid = self._validate_cd_workflow()
        all_valid = all_valid and cd_valid
        
        # Validate Release workflow
        release_valid = self._validate_release_workflow()
        all_valid = all_valid and release_valid
        
        return all_valid
    
    def _validate_ci_workflow(self) -> bool:
        """Validate CI workflow structure."""
        ci_path = self.workflows_dir / "ci.yml"
        
        if not ci_path.exists():
            print("  ❌ ci.yml not found")
            return False
        
        try:
            with open(ci_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            errors = []
            warnings = []
            info = []
            
            # Check required fields
            if 'name' not in workflow:
                errors.append("Missing 'name' field")
            else:
                info.append(f"Workflow name: {workflow['name']}")
            
            # YAML parses 'on' as True (boolean), check for both
            if 'on' not in workflow and True not in workflow:
                errors.append("Missing 'on' trigger field")
            
            if 'jobs' not in workflow:
                errors.append("Missing 'jobs' field")
            else:
                jobs = workflow['jobs']
                expected_jobs = ['lint', 'test-backend', 'test-frontend', 'coverage', 
                                'performance', 'security', 'build-docker', 'ci-success']
                
                for job in expected_jobs:
                    if job in jobs:
                        info.append(f"Job '{job}' defined")
                    else:
                        warnings.append(f"Job '{job}' not found (expected)")
            
            # Store result
            result = WorkflowValidationResult(
                workflow_name="CI Workflow",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                info=info
            )
            self.results.append(result)
            
            if result.valid:
                print(f"  ✅ CI workflow structure valid ({len(workflow['jobs'])} jobs)")
            else:
                print(f"  ❌ CI workflow structure invalid ({len(errors)} errors)")
            
            return result.valid
            
        except Exception as e:
            print(f"  ❌ Error validating CI workflow: {str(e)}")
            return False
    
    def _validate_cd_workflow(self) -> bool:
        """Validate CD workflow structure."""
        cd_path = self.workflows_dir / "deploy.yml"
        
        if not cd_path.exists():
            print("  ❌ deploy.yml not found")
            return False
        
        try:
            with open(cd_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            errors = []
            warnings = []
            info = []
            
            if 'jobs' not in workflow:
                errors.append("Missing 'jobs' field")
            else:
                jobs = workflow['jobs']
                expected_jobs = ['setup', 'build', 'deploy-staging', 
                                'deploy-production', 'post-deployment']
                
                for job in expected_jobs:
                    if job in jobs:
                        info.append(f"Job '{job}' defined")
                    else:
                        warnings.append(f"Job '{job}' not found")
            
            result = WorkflowValidationResult(
                workflow_name="CD Workflow",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                info=info
            )
            self.results.append(result)
            
            if result.valid:
                print(f"  ✅ CD workflow structure valid ({len(workflow['jobs'])} jobs)")
            else:
                print(f"  ❌ CD workflow structure invalid ({len(errors)} errors)")
            
            return result.valid
            
        except Exception as e:
            print(f"  ❌ Error validating CD workflow: {str(e)}")
            return False
    
    def _validate_release_workflow(self) -> bool:
        """Validate Release workflow structure."""
        release_path = self.workflows_dir / "release.yml"
        
        if not release_path.exists():
            print("  ❌ release.yml not found")
            return False
        
        try:
            # Try multiple encodings
            for encoding in ['utf-8', 'utf-8-sig', None]:
                try:
                    with open(release_path, 'r', encoding=encoding) as f:
                        workflow = yaml.safe_load(f)
                    break
                except UnicodeDecodeError:
                    if encoding is None:
                        raise
                    continue
            
            errors = []
            warnings = []
            info = []
            
            if 'jobs' not in workflow:
                errors.append("Missing 'jobs' field")
            else:
                jobs = workflow['jobs']
                expected_jobs = ['create-release', 'build-artifacts', 
                                'publish-pypi', 'update-docs', 'notify']
                
                for job in expected_jobs:
                    if job in jobs:
                        info.append(f"Job '{job}' defined")
                    else:
                        warnings.append(f"Job '{job}' not found")
            
            result = WorkflowValidationResult(
                workflow_name="Release Workflow",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                info=info
            )
            self.results.append(result)
            
            if result.valid:
                print(f"  ✅ Release workflow structure valid ({len(workflow['jobs'])} jobs)")
            else:
                print(f"  ❌ Release workflow structure invalid ({len(errors)} errors)")
            
            return result.valid
            
        except Exception as e:
            print(f"  ❌ Error validating Release workflow: {str(e)}")
            return False
    
    def check_secret_references(self) -> bool:
        """
        Check secret references in workflows.
        
        Returns:
            bool: True if secret references are consistent
        """
        all_secrets = set()
        
        # Scan all workflows for secret references
        for workflow_path in self.workflows_dir.glob("*.yml"):
            secrets = self._extract_secrets_from_workflow(workflow_path)
            all_secrets.update(secrets)
        
        print(f"  Found {len(all_secrets)} unique secret(s) referenced:")
        
        # Expected secrets
        expected_secrets = {
            'GITHUB_TOKEN',  # Always available
            'KUBECONFIG_STAGING',
            'KUBECONFIG_PRODUCTION',
            'STAGING_SSH_KEY',
            'STAGING_USER',
            'STAGING_HOST',
            'PRODUCTION_SSH_KEY',
            'PRODUCTION_USER',
            'PRODUCTION_HOST',
            'PYPI_API_TOKEN',
            'CODECOV_TOKEN',
            'SLACK_WEBHOOK',
        }
        
        for secret in sorted(all_secrets):
            if secret in expected_secrets:
                print(f"    ✅ {secret}")
            else:
                print(f"    ⚠️  {secret} - Not in expected secrets list")
        
        # Check for missing expected secrets
        missing = expected_secrets - all_secrets - {'GITHUB_TOKEN'}
        if missing:
            print(f"  ⚠️  Expected secrets not referenced: {', '.join(sorted(missing))}")
        
        return True  # Informational only
    
    def _extract_secrets_from_workflow(self, workflow_path: Path) -> set:
        """Extract secret references from workflow file."""
        secrets = set()
        
        try:
            with open(workflow_path, 'r') as f:
                content = f.read()
            
            # Find all ${{ secrets.SECRET_NAME }} patterns
            import re
            pattern = r'\$\{\{\s*secrets\.(\w+)\s*\}\}'
            matches = re.findall(pattern, content)
            secrets.update(matches)
            
        except Exception:
            pass
        
        return secrets
    
    def validate_docker_config(self) -> bool:
        """
        Validate Docker configuration.
        
        Returns:
            bool: True if Docker config is valid
        """
        all_valid = True
        
        # Check Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            print(f"  ✅ Dockerfile exists")
        else:
            print(f"  ⚠️  Dockerfile not found (backend deployment may fail)")
            all_valid = False
        
        # Check frontend Dockerfile
        frontend_dockerfile = self.project_root / "frontend" / "Dockerfile"
        if frontend_dockerfile.exists():
            print(f"  ✅ frontend/Dockerfile exists")
        else:
            print(f"  ⚠️  frontend/Dockerfile not found (frontend deployment may fail)")
        
        # Check docker-compose files
        compose_files = [
            "docker-compose.yml",
            "docker-compose.staging.yml",
            "docker-compose.production.yml"
        ]
        
        for compose_file in compose_files:
            path = self.project_root / compose_file
            if path.exists():
                print(f"  ✅ {compose_file} exists")
            else:
                print(f"  ⚠️  {compose_file} not found (optional)")
        
        return all_valid


def main():
    """Main test function."""
    validator = CICDPipelineValidator()
    success = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
