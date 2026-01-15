# Contributing to Scope

Thank you for your interest in contributing to Scope! This document provides guidelines and instructions for contributing.

## 🎯 Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community.

## 🚀 How to Contribute

### 1. Reporting Issues
- Check if the issue already exists in the [GitHub Issues](https://github.com/NickAiNYC/Scope/issues)
- Use the issue templates if available
- Include:
  - Clear description of the problem
  - Steps to reproduce
  - Expected vs actual behavior
  - Screenshots if applicable
  - Environment details (OS, Python version, etc.)

### 2. Feature Requests
- Explain the feature and its use case
- Describe the expected behavior
- Consider if it aligns with project goals

### 3. Pull Requests
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Ensure code passes existing tests
6. Update documentation
7. Submit a pull request

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- Git

### Installation
```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/Scope.git
cd Scope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_gap_detector.py

# Run with coverage
pytest --cov=core tests/
```

### Code Style
We use:
- **Ruff** for linting and formatting
- **Black**-compatible style (enforced by Ruff)
- **PEP 8** conventions

```bash
# Check code style
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
ruff format .
```

## 📁 Project Structure

```
Scope/
├── app.py              # Main Streamlit application
├── core/               # Core AI engine
├── violations/         # NYC DOB violation management
├── tests/              # Test files
├── data/               # Mock data
└── docs/               # Documentation
```

## 🧪 Testing Guidelines

- Write tests for new functionality
- Maintain or improve test coverage
- Tests should be fast and isolated
- Use pytest fixtures for common setup

## 📝 Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update API documentation if needed
- Keep comments clear and concise

## 🏗️ Architecture Principles

1. **Modularity**: Keep components decoupled
2. **Testability**: Write testable code
3. **Documentation**: Document public APIs
4. **Performance**: Consider efficiency for large datasets
5. **Security**: Never commit secrets or API keys

## 🔄 Pull Request Process

1. Ensure your code passes all tests
2. Update documentation
3. Add a descriptive title and summary
4. Reference related issues
5. Wait for review and address feedback

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

Thank you for contributing to open source and helping improve construction compliance automation!
