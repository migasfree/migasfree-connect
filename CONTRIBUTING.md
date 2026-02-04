# Contributing to Migasfree Connect

Thank you for your interest in contributing to Migasfree Connect! We ❤️ changes and improvements.

## Code of Conduct

Please be respectful and professional in all interactions.

## How to Contribute

1. **Report Bugs**: Open an issue on GitHub with a clear description and steps to reproduce.
2. **Suggest Enhancements**: Open an issue to discuss new features.
3. **Pull Requests**:
    * Fork the repository.
    * Create a feature branch (`git checkout -b feature/amazing-feature`).
    * Commit your changes (`git commit -m 'Add some amazing feature'`).
    * Push to the branch (`git push origin feature/amazing-feature`).
    * Open a Pull Request.

## Development Setup

### Requirements

* Python 3.8+
* OpenSSL (for certificate handling)

### Installation

```bash
# Clone the repository
git clone https://github.com/migasfree/migasfree-connect.git
cd migasfree-connect

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Quality Standards

### Testing

We use `pytest`. All new features should include unit tests.

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=migasfree_connect tests/
```

### Linting & Formatting

We use `ruff` for linting and formatting.

```bash
# Lint code
ruff check .

# Format code
ruff format .
```

### Architectural Decisions

Major architectural changes should be documented using Architecture Decision Records (ADRs) in the `docs/adr/` directory.

---
migasfree -- we ❤️ change
