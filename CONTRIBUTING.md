# Contributing to ClarifAI

Thank you for your interest in contributing to ClarifAI! This document provides guidelines for contributing to our monorepo.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (latest version)
- Git

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/robbiemu/clarifAI.git
   cd clarifAI
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

## Monorepo Structure

ClarifAI is organized as a monorepo with the following structure:

```
clarifAI/
├── docs/                    # Documentation
├── services/                # Individual services
│   ├── clarifai-core/      # Main processing engine
│   ├── vault-watcher/      # File monitoring service
│   ├── scheduler/          # Task scheduling service
│   └── clarifai-ui/        # Gradio web interface
├── shared/                  # Shared utilities and models
├── tests/                   # Integration tests
└── pyproject.toml          # Root project configuration
```

## Working with Services

Each service is a separate Python package that can be developed independently:

### Installing All Services
```bash
poetry install
```

### Running Tests
```bash
# All tests
poetry run pytest

# Specific service tests
cd services/clarifai-core
poetry run pytest
```

### Code Quality
```bash
# Run all quality checks
poetry run ruff check .
poetry run black --check .
poetry run mypy .

# Auto-fix formatting issues
poetry run ruff check --fix .
poetry run black .
```

## Development Workflow

1. **Create a Feature Branch**: Always work on a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**: Focus on one feature or fix per branch

3. **Test Your Changes**: Ensure all tests pass and code quality checks succeed
   ```bash
   poetry run pytest
   poetry run ruff check .
   poetry run black --check .
   ```

4. **Commit Your Changes**: Use clear, descriptive commit messages
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**: Push your branch and create a pull request

## Code Style

We use several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **Black**: Code formatting
- **MyPy**: Static type checking
- **pre-commit**: Automated quality checks

### Style Guidelines

- Follow Python PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep line length to 88 characters
- Use descriptive variable and function names

## Testing

- Write tests for all new functionality
- Ensure tests cover edge cases
- Use descriptive test names and docstrings
- Maintain or improve test coverage

### Test Structure

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_structure.py
```

## Service-Specific Development

### clarifai-core
Main processing engine for AI operations. See `services/clarifai-core/README.md` for detailed information.

### vault-watcher
File monitoring service. See `services/vault-watcher/README.md` for detailed information.

### scheduler
Task scheduling service. See `services/scheduler/README.md` for detailed information.

### clarifai-ui
Gradio web interface. See `services/clarifai-ui/README.md` for detailed information.

## Shared Components

The `shared/` directory contains common utilities and data models used across services:

- `shared/models/`: Data models and schemas
- `shared/config/`: Configuration management
- `shared/utils/`: Utility functions
- `shared/database/`: Database interfaces
- `shared/messaging/`: Message queue utilities

## Pull Request Guidelines

1. **Clear Description**: Provide a clear description of what your PR does
2. **Reference Issues**: Link to any relevant issues
3. **Test Coverage**: Ensure adequate test coverage for new code
4. **Documentation**: Update documentation for user-facing changes
5. **Breaking Changes**: Clearly document any breaking changes

## Commit Message Format

Use conventional commit format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (no logic changes)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example: `feat(core): add new claim extraction algorithm`

## Questions and Support

- Check existing issues and documentation first
- Create an issue for bugs or feature requests
- Join discussions in existing issues
- Be respectful and constructive in all interactions

## License

By contributing to ClarifAI, you agree that your contributions will be licensed under the MIT License.