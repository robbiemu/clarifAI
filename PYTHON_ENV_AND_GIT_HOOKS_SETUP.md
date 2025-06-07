# Python Environment (uv) and Git Hooks (pre-commit) Setup

This document outlines the recommended steps to set up a consistent Python development environment using `uv` and to enforce code quality using pre-commit hooks.

## Python Environment with `uv`

`uv` is a fast Python package installer and resolver. For this monorepo, you can manage environments per service or explore `uv`'s capabilities for workspace management as they evolve.

### Basic `uv` Setup (per service)

For each service in the `services/` directory (and potentially for the `shared/` directory if it were to have its own direct dependencies):

1.  **Navigate to the service directory:**
    ```bash
    cd services/<service_name>
    ```

2.  **Create a virtual environment:**
    ```bash
    uv venv
    ```
    This will create a `.venv` directory. Ensure `.venv/` is in your service-specific `.gitignore` or the root `.gitignore`.

3.  **Activate the virtual environment:**
    *   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows (Git Bash or WSL):
        ```bash
        source .venv/Scripts/activate
        ```
    *   On Windows (Command Prompt):
        ```bash
        .venv\Scripts\activate.bat
        ```
    *   On Windows (PowerShell):
        ```bash
        .venv\Scripts\Activate.ps1
        ```

4.  **Install dependencies:**
    Create a `requirements.txt` or `pyproject.toml` in the service directory.
    *   Using `requirements.txt`:
        ```bash
        uv pip install -r requirements.txt
        ```
    *   Using `pyproject.toml` (if you define dependencies there):
        ```bash
        uv pip install .
        ```
        (Or `uv pip install -e .` for an editable install)

### Monorepo-wide `uv` Configuration (Future Consideration)

As `uv` evolves, features for monorepo workspace management might become more prominent. Refer to the official `uv` documentation for the latest best practices on managing multi-package repositories.

## Git Pre-commit Hooks

Pre-commit hooks help ensure code quality and consistency before commits are made.

1.  **Install pre-commit:**
    ```bash
    pip install pre-commit
    # or using uv once it supports global tool installation or you are in an active venv
    # uv pip install pre-commit
    ```

2.  **Create a pre-commit configuration file:**
    Create a file named `.pre-commit-config.yaml` in the **root** of the monorepo with the following example content:

    ```yaml
    # .pre-commit-config.yaml
    repos:
    -   repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.6.0 # Use the latest version
        hooks:
        -   id: check-yaml
        -   id: end-of-file-fixer
        -   id: trailing-whitespace
    -   repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.4.4 # Use the latest version
        hooks:
        -   id: ruff # Runs a comprehensive set of linters
          args: [--fix, --exit-non-zero-on-fix]
        -   id: ruff-format # Formats code
    # -   repo: https://github.com/psf/black-pre-commit-mirror # Or use black if preferred over ruff-format
    #     rev: 24.4.2 # Use the latest version for black
    #     hooks:
    #     -   id: black
    ```

3.  **Install the git hooks:**
    Navigate to the root of the monorepo and run:
    ```bash
    pre-commit install
    ```

Now, the configured hooks will run automatically on `git commit`. You can also run them manually at any time:
```bash
pre-commit run --all-files
```

This setup provides a good starting point. You can customize the `.pre-commit-config.yaml` file to add or remove hooks based on project needs.
