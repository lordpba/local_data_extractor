# Contributing to AI-Powered Document Data Extractor

First off, thank you for considering contributing to this project! 🎉

The following is a set of guidelines for contributing. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct

This project and everyone participating in it is governed by respect and professionalism. Be kind, be constructive, and help create a welcoming environment for everyone.

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title** - Describe the issue in one line
- **Steps to reproduce** - What did you do?
- **Expected behavior** - What should have happened?
- **Actual behavior** - What actually happened?
- **Environment** - OS, Python version, Ollama version, model used
- **Logs** - Any error messages or stack traces

**Example:**
```
Title: "PDF processing fails with multi-page documents on Windows"

Steps:
1. Upload a 5-page PDF via web interface
2. Click "Extract Data"
3. Error occurs on page 3

Expected: All 5 pages processed
Actual: Error: "poppler not found"

Environment:
- Windows 11
- Python 3.11
- Ollama 0.1.17
- Model: llava:latest

Logs:
[error stack trace here]
```

### 💡 Suggesting Features

Feature requests are welcome! Please include:

- **Use case** - What problem does this solve?
- **Proposed solution** - How would it work?
- **Alternatives** - What other approaches did you consider?
- **Impact** - Who benefits from this feature?

### 🔧 Contributing Code

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages** (see guidelines below)
6. **Push to your fork** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Ollama installed and running
- poppler-utils (for PDF processing)
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# For Ollama version
cd Ollama
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Pull a test model
ollama pull llava:latest

# Run the application
python app.py
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python test_ollama.py
```

## 📝 Coding Guidelines

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Maximum line length: **100 characters**
- Use **docstrings** for functions and classes

**Example:**
```python
def process_document(file_path: str, mime_type: str) -> Dict[str, Any]:
    """
    Process a document and extract images.
    
    Args:
        file_path: Absolute path to the document file
        mime_type: MIME type of the document
        
    Returns:
        Dictionary containing processed pages and metadata
        
    Raises:
        ValueError: If file format is not supported
    """
    # Implementation here
    pass
```

### Code Organization

- **Keep functions small** - One function, one purpose
- **Avoid deep nesting** - Max 3 levels of indentation
- **Use meaningful names** - `extract_invoice_data()` not `eid()`
- **Add comments for complex logic** - But code should be self-documenting

### Error Handling

```python
# Good: Specific exception, helpful message
try:
    result = process_pdf(file_path)
except FileNotFoundError:
    logger.error(f"PDF file not found: {file_path}")
    raise ValueError(f"Cannot process missing file: {file_path}")

# Bad: Bare except, no context
try:
    result = process_pdf(file_path)
except:
    print("Error")
```

### Testing

- Write tests for new features
- Update tests when fixing bugs
- Aim for >80% code coverage
- Test edge cases and error conditions

## 📦 Commit Messages

Use clear, descriptive commit messages following this format:

```
<type>: <short summary> (max 72 characters)

<detailed explanation if needed>

<footer: references to issues, breaking changes>
```

### Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic change)
- `refactor:` - Code refactoring (no feature change)
- `perf:` - Performance improvement
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Examples

```
feat: add confidence score filtering in web UI

Users can now set a minimum confidence threshold to flag
low-confidence extractions for manual review.

Closes #42
```

```
fix: handle corrupted PDF files gracefully

Previously crashed with unclear error. Now shows user-friendly
message and continues processing other files.

Fixes #38
```

```
docs: update Ollama setup guide with Windows instructions

Added WSL setup steps and troubleshooting section for
Windows users.
```

## 🔄 Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Added/updated tests as needed
- [ ] All tests pass locally
- [ ] Updated documentation if needed
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive data or credentials in code
- [ ] Feature branch is up to date with main

### PR Template

When opening a PR, include:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How did you test this? What cases did you cover?

## Screenshots (if applicable)
For UI changes, include before/after screenshots

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated checks** - CI/CD tests must pass
2. **Code review** - At least one maintainer approval needed
3. **Testing** - Maintainers may test your changes
4. **Feedback** - Address review comments promptly
5. **Merge** - Maintainer will merge once approved

### After Merge

- Your contribution will be included in the next release
- You'll be added to contributors list
- Thank you! 🎉

## 🎯 Good First Issues

Look for issues labeled `good first issue` - these are great starting points for new contributors:

- Documentation improvements
- Adding examples
- Minor bug fixes
- UI enhancements
- Test coverage improvements

## 💬 Questions?

- 📖 Check the [documentation](README.md)
- 💬 Open a discussion on GitHub
- 📧 Contact maintainers

## 🙏 Recognition

Contributors will be:
- Listed in README acknowledgments
- Mentioned in release notes
- Given credit in commits

Thank you for making this project better! 🚀

---

<div align="center">

**[⬆ Back to Top](#contributing-to-ai-powered-document-data-extractor)** | **[📘 Main Docs](README.md)**

</div>
