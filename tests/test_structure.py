"""Test that all services have valid structure."""

from pathlib import Path

import pytest


def test_service_structure():
    """Test that all services have the expected directory structure."""
    repo_root = Path(__file__).parent.parent
    services_dir = repo_root / "services"

    expected_services = ["clarifai-core", "vault-watcher", "scheduler", "clarifai-ui"]

    for service_name in expected_services:
        service_dir = services_dir / service_name
        assert service_dir.exists(), f"Service directory {service_name} not found"

        # Check for pyproject.toml
        pyproject_file = service_dir / "pyproject.toml"
        assert pyproject_file.exists(), f"pyproject.toml not found in {service_name}"

        # Check for README.md
        readme_file = service_dir / "README.md"
        assert readme_file.exists(), f"README.md not found in {service_name}"


def test_service_modules_exist():
    """Test that each service has its main module directory."""
    repo_root = Path(__file__).parent.parent
    services_dir = repo_root / "services"

    service_modules = {
        "clarifai-core": "clarifai_core",
        "vault-watcher": "clarifai_vault_watcher",
        "scheduler": "clarifai_scheduler",
        "clarifai-ui": "clarifai_ui",
    }

    for service_name, module_name in service_modules.items():
        service_package_dir = services_dir / service_name / module_name
        assert (
            service_package_dir.exists()
        ), f"Module directory {module_name} not found in {service_name}"

        # Check for __init__.py
        init_file = service_package_dir / "__init__.py"
        assert (
            init_file.exists()
        ), f"__init__.py not found in {service_name}/{module_name}"


def test_shared_package():
    """Test that shared package can be imported."""
    # This test relies on the test runner (pytest) having 'shared' in its PYTHONPATH.
    # This is typically handled by installing the 'shared' package in editable mode
    # or by pytest's Python path manipulation if 'shared' is a top-level directory
    # recognized by the project structure (e.g. via uv.workspace).
    try:
        import clarifai_shared  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import clarifai_shared package: {e}")


def test_project_structure():
    """Test that the project has the expected monorepo structure."""
    repo_root = Path(__file__).parent.parent

    # Check essential files
    essential_files = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        ".gitignore",
        ".pre-commit-config.yaml",
    ]

    for file_name in essential_files:
        file_path = repo_root / file_name
        assert file_path.exists(), f"Essential file {file_name} not found at root"

    # Check essential directories
    essential_dirs = ["docs", "services", "shared", "tests"]

    for dir_name in essential_dirs:
        dir_path = repo_root / dir_name
        assert dir_path.exists(), f"Essential directory {dir_name} not found at root"
