#!/usr/bin/env python3
"""
GitHub Actions Validation Script

This script validates that your Gomu News Monitor is correctly configured
for deployment to GitHub Actions.

Usage:
    python scripts/validate_github_actions.py

Exit Codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import yaml
import subprocess


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []

    def add_pass(self, message: str):
        """Add a passed check."""
        self.checks_passed.append(message)

    def add_fail(self, message: str, details: str = None):
        """Add a failed check."""
        self.checks_failed.append((message, details))

    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

    def is_success(self) -> bool:
        """Check if all validations passed."""
        return len(self.checks_failed) == 0

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        # Passed checks
        if self.checks_passed:
            print(f"\n[PASS] {len(self.checks_passed)} checks passed:")
            for check in self.checks_passed:
                print(f"   [+] {check}")

        # Warnings
        if self.warnings:
            print(f"\n[WARN] {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"   [!] {warning}")

        # Failed checks
        if self.checks_failed:
            print(f"\n[FAIL] {len(self.checks_failed)} checks failed:")
            for check, details in self.checks_failed:
                print(f"   [-] {check}")
                if details:
                    print(f"       Details: {details}")

        # Final result
        print("\n" + "=" * 70)
        if self.is_success():
            print("SUCCESS: ALL VALIDATIONS PASSED!")
            print("Your project is ready for GitHub Actions deployment.")
            print("\nNext steps:")
            print("  1. Commit all files: git add . && git commit -m 'Setup GitHub Actions'")
            print("  2. Create GitHub repository (if not exists)")
            print("  3. Push to GitHub: git push origin main")
            print("  4. Configure GitHub Secrets (see GITHUB_ACTIONS_SETUP.md)")
            print("  5. Enable Actions in your GitHub repository")
        else:
            print("FAILED: VALIDATION FAILED")
            print("Please fix the issues above before deploying to GitHub Actions.")
            print("\nFor help, see: GITHUB_ACTIONS_SETUP.md")
        print("=" * 70 + "\n")


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def validate_workflow_yaml(result: ValidationResult) -> None:
    """Validate GitHub Actions workflow YAML file."""
    print("\n[*] Checking GitHub Actions workflow configuration...")

    workflow_path = get_project_root() / ".github" / "workflows" / "monitor.yml"

    if not workflow_path.exists():
        result.add_fail(
            "Workflow file not found",
            f"Expected: {workflow_path}"
        )
        return

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = yaml.safe_load(f)

        # Check for required keys
        # Note: 'on' is parsed as boolean True in YAML
        required_keys = ['name', 'jobs']
        for key in required_keys:
            if key not in workflow_data:
                result.add_fail(
                    f"Workflow missing required key: {key}",
                    f"File: {workflow_path}"
                )
                return

        # Check for 'on' key (may be parsed as True in YAML)
        if 'on' not in workflow_data and True not in workflow_data:
            result.add_fail(
                "Workflow missing 'on' trigger configuration",
                f"File: {workflow_path}"
            )
            return

        # Get the 'on' configuration (may be stored as True in YAML)
        on_config = workflow_data.get('on', workflow_data.get(True, {}))

        # Check schedule is configured
        if 'schedule' in on_config:
            result.add_pass("Workflow has cron schedule configured")
        else:
            result.add_warning("No cron schedule found in workflow (only manual triggers)")

        # Check workflow_dispatch is enabled
        if 'workflow_dispatch' in on_config:
            result.add_pass("Manual workflow trigger (workflow_dispatch) enabled")
        else:
            result.add_warning("Manual workflow trigger not enabled")

        # Check for required steps
        jobs = workflow_data.get('jobs', {})
        if 'monitor' in jobs:
            steps = jobs['monitor'].get('steps', [])
            step_names = [step.get('name', '') for step in steps]

            required_steps = [
                'Checkout',
                'Python',
                'Chrome',
                'dependencies',
                'env',
                'monitoring'
            ]

            for required in required_steps:
                if any(required.lower() in name.lower() for name in step_names):
                    result.add_pass(f"Workflow has {required} step")
                else:
                    result.add_fail(
                        f"Workflow missing {required} step",
                        "This step is required for proper execution"
                    )
        else:
            result.add_fail(
                "Workflow missing 'monitor' job",
                "Expected a job named 'monitor'"
            )

        result.add_pass("Workflow YAML syntax is valid")

    except yaml.YAMLError as e:
        result.add_fail(
            "Invalid YAML syntax in workflow file",
            str(e)
        )
    except Exception as e:
        result.add_fail(
            "Error reading workflow file",
            str(e)
        )


def validate_gitignore(result: ValidationResult) -> None:
    """Validate .gitignore file."""
    print("\n[*] Checking .gitignore configuration...")

    gitignore_path = get_project_root() / ".gitignore"

    if not gitignore_path.exists():
        result.add_fail(
            ".gitignore file not found",
            "Critical security issue - secrets may be committed!"
        )
        return

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()

        # Check for critical patterns
        critical_patterns = {
            '.env': 'Environment files',
            'data/': 'Data directory',
            'logs/': 'Logs directory',
            '*.db': 'Database files',
            '.wdm/': 'ChromeDriver cache'
        }

        for pattern, description in critical_patterns.items():
            if pattern in gitignore_content:
                result.add_pass(f".gitignore includes {description} ({pattern})")
            else:
                result.add_fail(
                    f".gitignore missing pattern: {pattern}",
                    f"This could expose {description}"
                )

        # Check if .env.example is allowed
        if '!.env.example' in gitignore_content or '.env.example' not in gitignore_content:
            result.add_pass(".env.example is allowed (good for documentation)")

    except Exception as e:
        result.add_fail(
            "Error reading .gitignore file",
            str(e)
        )


def validate_config_yaml(result: ValidationResult) -> None:
    """Validate config.yaml settings for GitHub Actions."""
    print("\n[*] Checking config.yaml settings...")

    config_path = get_project_root() / "config.yaml"

    if not config_path.exists():
        result.add_fail(
            "config.yaml not found",
            f"Expected: {config_path}"
        )
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Check scraping.headless is true
        headless = config_data.get('scraping', {}).get('headless', None)
        if headless is True:
            result.add_pass("config.yaml has headless mode enabled")
        else:
            result.add_fail(
                "config.yaml: scraping.headless must be true",
                "GitHub Actions requires headless browser mode"
            )

        # Check reasonable timeout settings
        timeout = config_data.get('monitoring', {}).get('request_timeout_seconds', 30)
        if timeout >= 60:
            result.add_pass(f"Request timeout is {timeout}s (good for GitHub Actions)")
        else:
            result.add_warning(
                f"Request timeout is {timeout}s - consider increasing to 60s for GitHub Actions"
            )

        # Check delay settings
        delay_min = config_data.get('scraping', {}).get('delay_between_requests_min', 1)
        delay_max = config_data.get('scraping', {}).get('delay_between_requests_max', 3)

        if delay_min >= 2 and delay_max >= 4:
            result.add_pass(f"Request delays are {delay_min}-{delay_max}s (good for rate limiting)")
        else:
            result.add_warning(
                f"Request delays are {delay_min}-{delay_max}s - consider 2-4s for GitHub Actions"
            )

        # Check auth settings
        auth_enabled = config_data.get('auth', {}).get('enabled', True)
        auth_continue = config_data.get('auth', {}).get('continue_on_failure', True)

        if not auth_enabled or auth_continue:
            result.add_pass("Auth configured to continue on failure (recommended)")
        else:
            result.add_warning(
                "Auth will stop on failure - consider setting auth.continue_on_failure: true"
            )

    except yaml.YAMLError as e:
        result.add_fail(
            "Invalid YAML syntax in config.yaml",
            str(e)
        )
    except Exception as e:
        result.add_fail(
            "Error reading config.yaml",
            str(e)
        )


def validate_env_not_committed(result: ValidationResult) -> None:
    """Validate that .env file is not committed to git."""
    print("\n[*] Checking that secrets are not committed...")

    env_path = get_project_root() / ".env"

    # Check if .env exists
    if env_path.exists():
        # Check if it's tracked by git
        try:
            git_result = subprocess.run(
                ['git', 'ls-files', '--error-unmatch', '.env'],
                cwd=get_project_root(),
                capture_output=True,
                text=True
            )

            if git_result.returncode == 0:
                result.add_fail(
                    ".env file is tracked by git!",
                    "CRITICAL: Remove it with 'git rm --cached .env'"
                )
            else:
                result.add_pass(".env file exists but not tracked by git (good)")

        except FileNotFoundError:
            result.add_warning("Git not found - cannot verify .env is not tracked")
        except Exception as e:
            result.add_warning(f"Could not check git status: {e}")
    else:
        result.add_pass(".env file not found (will be created by GitHub Actions)")

    # Check if .env.example exists
    env_example_path = get_project_root() / ".env.example"
    if env_example_path.exists():
        result.add_pass(".env.example exists (good for documentation)")
    else:
        result.add_warning(".env.example not found - consider creating one")


def validate_secrets_documentation(result: ValidationResult) -> None:
    """Validate that secrets are properly documented."""
    print("\n[*] Checking secrets documentation...")

    setup_doc_path = get_project_root() / "GITHUB_ACTIONS_SETUP.md"

    if not setup_doc_path.exists():
        result.add_fail(
            "GITHUB_ACTIONS_SETUP.md not found",
            "Users need documentation to configure GitHub Secrets"
        )
        return

    try:
        with open(setup_doc_path, 'r', encoding='utf-8') as f:
            doc_content = f.read()

        # Check for required secrets documentation
        required_secrets = [
            'LOGIN_EMAIL',
            'LOGIN_PASSWORD',
            'EMAIL_FROM',
            'EMAIL_PASSWORD',
            'EMAIL_TO',
            'SMTP_SERVER',
            'SMTP_PORT'
        ]

        all_documented = True
        for secret in required_secrets:
            if secret in doc_content:
                result.add_pass(f"Secret {secret} is documented")
            else:
                result.add_fail(
                    f"Secret {secret} not documented in setup guide",
                    "Users need to know about all required secrets"
                )
                all_documented = False

        if all_documented:
            result.add_pass("All 7 required secrets are documented")

    except Exception as e:
        result.add_fail(
            "Error reading GITHUB_ACTIONS_SETUP.md",
            str(e)
        )


def validate_required_files(result: ValidationResult) -> None:
    """Validate that all required files exist."""
    print("\n[*] Checking required files...")

    required_files = {
        'requirements.txt': 'Python dependencies',
        'config.yaml': 'Main configuration',
        'main.py': 'Entry point',
        'src/config.py': 'Config module',
        'src/database.py': 'Database module',
        'src/auth.py': 'Auth module',
        'src/scraper.py': 'Scraper module',
        'src/notifier.py': 'Notifier module',
        '.github/workflows/monitor.yml': 'GitHub Actions workflow',
        'GITHUB_ACTIONS_SETUP.md': 'Setup documentation'
    }

    project_root = get_project_root()

    for file_path, description in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            result.add_pass(f"{description} exists ({file_path})")
        else:
            result.add_fail(
                f"Required file missing: {file_path}",
                f"This file is needed for {description}"
            )


def validate_python_syntax(result: ValidationResult) -> None:
    """Validate Python syntax of main files."""
    print("\n[*] Checking Python syntax...")

    python_files = [
        'main.py',
        'src/config.py',
        'src/database.py',
        'src/auth.py',
        'src/scraper.py',
        'src/notifier.py'
    ]

    project_root = get_project_root()

    for file_path in python_files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
            result.add_pass(f"Python syntax valid: {file_path}")
        except SyntaxError as e:
            result.add_fail(
                f"Syntax error in {file_path}",
                f"Line {e.lineno}: {e.msg}"
            )
        except Exception as e:
            result.add_warning(f"Could not validate {file_path}: {e}")


def main():
    """Main validation function."""
    print("=" * 70)
    print("GitHub Actions Deployment Validation")
    print("Gomu News Monitor")
    print("=" * 70)

    result = ValidationResult()

    # Run all validation checks
    validate_required_files(result)
    validate_workflow_yaml(result)
    validate_gitignore(result)
    validate_config_yaml(result)
    validate_env_not_committed(result)
    validate_secrets_documentation(result)
    validate_python_syntax(result)

    # Print summary
    result.print_summary()

    # Exit with appropriate code
    sys.exit(0 if result.is_success() else 1)


if __name__ == "__main__":
    main()
