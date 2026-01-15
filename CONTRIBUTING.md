# 🤝 Contributing to SentinelScope

Thank you for your interest in contributing to SentinelScope! This guide will help you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

---

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, trolling, or discriminatory comments
- Publishing others' private information without permission
- Conduct that could be considered inappropriate in a professional setting

If you witness or experience unacceptable behavior, please contact nick@thrivai.ai.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

**Before submitting a bug report:**
1. Check the [FAQ](FAQ.md) for common issues
2. Search [existing issues](https://github.com/NickAiNYC/Sentinel-Scope/issues) to avoid duplicates
3. Update to the latest version and verify the bug persists

**When submitting a bug report, include:**
- **Clear title:** Brief description of the issue
- **Steps to reproduce:** Exact steps to trigger the bug
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happened
- **Environment:**
  - OS: (e.g., macOS 14.1, Windows 11, Ubuntu 22.04)
  - Python version: (e.g., 3.11.5)
  - Browser: (e.g., Chrome 120, Safari 17)
- **Screenshots:** If applicable
- **Error messages:** Full stack trace

**Example:**
```markdown
**Title:** API key validation fails with trailing whitespace

**Steps to Reproduce:**
1. Add DeepSeek API key to `.streamlit/secrets.toml` with a space at the end
2. Run `streamlit run main.py`
3. Try to analyze photos

**Expected:** System should trim whitespace and use the valid key
**Actual:** Error: "Invalid API key"

**Environment:** macOS 14.1, Python 3.11.5, Chrome 120
```

### 💡 Suggesting Features

**Before suggesting a feature:**
1. Check the [Roadmap](../README.md#-roadmap) for planned features
2. Search [existing feature requests](https://github.com/NickAiNYC/Sentinel-Scope/issues?q=is%3Aissue+label%3Aenhancement)

**When suggesting a feature:**
- **Use Case:** Describe the problem you're trying to solve
- **Proposed Solution:** How should the feature work?
- **Alternatives Considered:** What other approaches did you think about?
- **Mockups/Examples:** Wireframes, screenshots, or code examples (if applicable)

**Example:**
```markdown
**Title:** Add support for Excel export

**Use Case:** 
Many construction managers prefer analyzing data in Excel rather than CSV format. 
They need formulas, pivot tables, and charts that work better in .xlsx files.

**Proposed Solution:**
Add an "Export to Excel" button that generates a multi-sheet workbook:
- Sheet 1: Project summary
- Sheet 2: Gap analysis
- Sheet 3: Milestones
- Sheet 4: DOB violations

**Alternatives Considered:**
- CSV export (current solution, but lacks formatting)
- Google Sheets integration (requires OAuth setup)

**Technical Approach:**
Use the `openpyxl` library for Excel generation.
```

### 📝 Improving Documentation

Documentation improvements are always welcome! You can:
- Fix typos or unclear explanations
- Add examples or screenshots
- Expand the FAQ with common questions
- Translate documentation to other languages

Small documentation changes can be made directly via GitHub's web interface.

### 💻 Contributing Code

See [Development Setup](#development-setup) and [Pull Request Process](#pull-request-process) below.

---

## Development Setup

### Prerequisites
- **Python 3.10+** (3.11 or 3.12 recommended)
- **Git** for version control
- **DeepSeek API Key** (free tier available)
- **Supabase Account** (free tier available)
- **Code Editor** (VS Code, PyCharm, or similar)

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub (click "Fork" button)
# Then clone your fork:
git clone https://github.com/YOUR_USERNAME/Sentinel-Scope.git
cd Sentinel-Scope

# Add upstream remote to stay in sync:
git remote add upstream https://github.com/NickAiNYC/Sentinel-Scope.git
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it:
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov ruff mypy black isort
```

### Step 3: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys
# Use your favorite editor (nano, vim, VS Code, etc.)
nano .env
```

Add your credentials:
```env
DEEPSEEK_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
```

Also configure Streamlit secrets:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
nano .streamlit/secrets.toml
```

### Step 4: Set Up Database

1. Create a Supabase project at https://supabase.com
2. Run the schema SQL:
   - Open Supabase SQL Editor
   - Copy contents from `docs/schema.sql` (if it exists)
   - Execute the SQL
3. Get your credentials from Project Settings → API

### Step 5: Run the Application

```bash
# Start the Streamlit app
streamlit run main.py

# The app opens at http://localhost:8501
```

### Step 6: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=core --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
# or
start htmlcov/index.html  # Windows
```

### Step 7: Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

This automatically runs linters before each commit.

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications defined in `pyproject.toml`.

**Key Rules:**
- **Line length:** 88 characters (Black default)
- **Indentation:** 4 spaces (no tabs)
- **Naming:**
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Imports:** Organized by `isort`
  - Standard library
  - Third-party packages
  - Local imports

**Example:**
```python
# Good ✅
from typing import List
import streamlit as st
from core.models import Project

def calculate_compliance_score(milestones: List[str]) -> float:
    """Calculate overall compliance percentage."""
    return len(milestones) / TOTAL_MILESTONES * 100

# Bad ❌
def Calculate_Compliance(m):  # Wrong naming, no type hints, no docstring
    return len(m)/15*100  # Magic number
```

### Type Hints

All new functions must include type hints:

```python
# Good ✅
def classify_image(
    image_bytes: bytes, 
    project_type: str
) -> CaptureClassification:
    """Classify a construction site capture."""
    ...

# Bad ❌
def classify_image(image_bytes, project_type):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def detect_gaps(
    milestones: List[str], 
    project_type: str
) -> List[ComplianceGap]:
    """
    Identify missing milestones based on NYC Building Code requirements.
    
    Args:
        milestones: List of detected milestone names
        project_type: Type of construction project (e.g., "Commercial")
    
    Returns:
        List of compliance gaps with risk levels and remediation steps
    
    Raises:
        ValueError: If project_type is not supported
    
    Example:
        >>> detected = ["Foundation Inspection", "MEP Rough-in"]
        >>> gaps = detect_gaps(detected, "Commercial")
        >>> print(gaps[0].system)
        'Structural'
    """
    ...
```

### Error Handling

Use custom exceptions defined in `core/exceptions.py`:

```python
# Good ✅
from core.exceptions import APIKeyError, ClassificationError

try:
    result = classifier.classify_capture(image_bytes)
except APIKeyError as e:
    st.error(f"API key issue: {e}")
    st.stop()
except ClassificationError as e:
    st.warning(f"Classification failed: {e}, using fallback")
    result = fallback_classifier(image_bytes)

# Bad ❌
try:
    result = classifier.classify_capture(image_bytes)
except:  # Bare except
    pass  # Silent failure
```

### Code Formatting Tools

**Before committing, run:**

```bash
# Format code with Black
black core/ main.py tests/

# Sort imports with isort
isort core/ main.py tests/

# Check for linting issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking
mypy core/ --ignore-missing-imports
```

**Or use the pre-commit hook to do this automatically.**

---

## Testing Guidelines

### Test Structure

Tests are organized by module:
```
tests/
├── __init__.py
├── test_gap_detector.py    # Gap detection logic
├── test_classifier.py       # AI classification
├── test_dob_engine.py       # NYC DOB API integration
└── test_database.py         # Supabase operations
```

### Writing Tests

**Use Pytest conventions:**

```python
import pytest
from core.gap_detector import ComplianceGapEngine

def test_gap_detection_commercial():
    """Test gap detection for commercial projects."""
    engine = ComplianceGapEngine()
    
    detected = ["Foundation Inspection", "MEP Rough-in"]
    gaps = engine.detect_gaps(detected, "Commercial")
    
    assert len(gaps) > 0
    assert gaps[0].risk_level in ["Critical", "High", "Medium", "Low"]
    assert "BC" in gaps[0].nyc_code_ref  # Should reference NYC Building Code

def test_gap_detection_invalid_type():
    """Test that invalid project types raise ValueError."""
    engine = ComplianceGapEngine()
    
    with pytest.raises(ValueError, match="Unsupported project type"):
        engine.detect_gaps([], "InvalidType")
```

### Test Coverage Goals

- **Overall:** 80%+ coverage
- **Critical paths:** 100% coverage
  - Gap detection logic
  - Risk scoring algorithm
  - API key validation
- **UI code:** Coverage not required (Streamlit components are hard to test)

### Running Specific Tests

```bash
# Run a single test file
pytest tests/test_gap_detector.py -v

# Run a specific test
pytest tests/test_gap_detector.py::test_gap_detection_commercial -v

# Run tests matching a pattern
pytest -k "gap_detection" -v

# Run with print statements visible
pytest tests/ -v -s
```

### Mocking External APIs

Use `pytest-mock` to avoid hitting real APIs in tests:

```python
def test_classifier_api_call(mocker):
    """Test that classifier calls DeepSeek API correctly."""
    # Mock the OpenAI client
    mock_client = mocker.patch('openai.OpenAI')
    mock_response = mocker.Mock()
    mock_response.choices[0].message.content = '{"milestone": "Foundation", "confidence": 0.95}'
    mock_client.return_value.chat.completions.create.return_value = mock_response
    
    classifier = SiteClassifier(api_key="test_key")
    result = classifier.classify_capture(b"fake_image", "Commercial")
    
    assert result.milestone == "Foundation"
    assert result.confidence == 0.95
```

---

## Pull Request Process

### 1. Create a Feature Branch

```bash
# Make sure you're on main and up-to-date
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/my-awesome-feature
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `refactor/` for code refactoring
- `test/` for test additions/fixes

### 2. Make Your Changes

- Write clean, well-documented code
- Add tests for new functionality
- Update documentation if needed
- Follow the coding standards above

### 3. Test Your Changes

```bash
# Run tests
pytest tests/ -v

# Check code quality
ruff check .
mypy core/

# Format code
black core/ main.py tests/
isort core/ main.py tests/
```

### 4. Commit Your Changes

**Use conventional commit messages:**

```bash
# Format: <type>(<scope>): <description>

# Examples:
git commit -m "feat(classifier): add support for industrial projects"
git commit -m "fix(gap-detector): correct risk level calculation for MEP"
git commit -m "docs(readme): add section on batch processing"
git commit -m "test(classifier): add unit tests for confidence scoring"
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### 5. Push to Your Fork

```bash
git push origin feature/my-awesome-feature
```

### 6. Open a Pull Request

1. Go to your fork on GitHub
2. Click **"Compare & pull request"**
3. Fill out the PR template:

```markdown
## Description
Brief description of what this PR does.

## Motivation and Context
Why is this change needed? What problem does it solve?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
```

### 7. Code Review

- Maintainers will review your PR
- Address any feedback or requested changes
- Push updates to your branch (they'll appear in the PR automatically)
- Once approved, a maintainer will merge your PR

### 8. Stay in Sync

```bash
# Keep your fork up-to-date with upstream
git checkout main
git pull upstream main
git push origin main
```

---

## Project Structure

```
Sentinel-Scope/
├── core/                       # Core business logic
│   ├── classifier.py           # AI image classification
│   ├── gap_detector.py         # Compliance gap detection
│   ├── processor.py            # Batch image processing
│   ├── dob_engine.py           # NYC DOB API integration
│   ├── database.py             # Supabase database connector
│   ├── models.py               # Pydantic data models
│   ├── constants.py            # NYC Building Code milestones
│   ├── config.py               # Configuration and env vars
│   └── exceptions.py           # Custom exceptions
├── tests/                      # Unit and integration tests
│   ├── test_gap_detector.py
│   ├── test_classifier.py
│   └── ...
├── docs/                       # Documentation
│   ├── FAQ.md
│   ├── USAGE_GUIDE.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   └── CONTRIBUTING.md (this file)
├── .github/                    # GitHub workflows and configs
│   └── workflows/
│       ├── ci-cd.yml
│       ├── test.yml
│       └── lint.yml
├── assets/                     # Images and demo files
├── main.py                     # Main Streamlit application
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variable template
└── README.md                   # Project overview
```

### Key Files to Know

- **`main.py`:** Entry point for the Streamlit app
- **`core/gap_detector.py`:** Core compliance logic
- **`core/classifier.py`:** AI integration for image analysis
- **`core/database.py`:** Supabase CRUD operations
- **`core/constants.py`:** NYC Building Code milestone definitions
- **`tests/`:** All test files

---

## Development Tips

### Debugging Streamlit Apps

```python
# Add debug prints
import streamlit as st

st.write("Debug:", variable_name)
st.json(data_dict)  # Pretty-print JSON
st.dataframe(df)    # Visualize DataFrames
```

### Working with Supabase

```python
# Test database connection
from core.database import get_db_client

client = get_db_client()
response = client.table('projects').select('*').execute()
print(response.data)
```

### Testing AI Locally

```python
# Create a test script to avoid restarting Streamlit
from core.classifier import SiteClassifier

classifier = SiteClassifier(api_key="your_key")
with open('test_image.jpg', 'rb') as f:
    result = classifier.classify_capture(f.read(), "Commercial")
    print(result.milestone, result.confidence)
```

---

## Getting Help

### Resources
- **Documentation:** Read the [docs/](../docs/) folder
- **Issues:** Search [GitHub Issues](https://github.com/NickAiNYC/Sentinel-Scope/issues)
- **Discussions:** Start a discussion on GitHub
- **Email:** nick@thrivai.ai

### Questions?

Feel free to:
- Open a [GitHub Discussion](https://github.com/NickAiNYC/Sentinel-Scope/discussions)
- Ask in the project's Slack channel
- Email the maintainer

---

## Recognition

Contributors will be:
- Listed in the README's "Acknowledgments" section
- Credited in release notes
- Given a shout-out on social media (if desired)

---

## License

By contributing to SentinelScope, you agree that your contributions will be licensed under the **MIT License**.

---

**Thank you for contributing! 🙏**

Your efforts help make construction compliance easier for contractors across NYC and beyond.
