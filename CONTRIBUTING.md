# Contributing to Zeus EAA Compliance Tool

Thank you for your interest in contributing to the Zeus EAA Compliance Tool! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
1. Check existing issues to avoid duplicates
2. Use the appropriate issue template
3. Provide detailed information about your environment
4. Include logs and error messages when applicable

### Submitting Pull Requests
1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following our coding standards
4. Test your changes thoroughly
5. Update documentation as needed
6. Submit a pull request using our template

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Azure CLI
- kubectl
- Git

### Local Development
```bash
# Clone your fork
git clone https://github.com/your-username/TRANSCRIBE.git
cd TRANSCRIBE

# Set up development environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r zeus-web-ui/requirements.txt
pip install -r zeus-aks-integration/requirements.txt

# Create development symlink
ln -sf zeus-aks-integration zeus_aks_integration

# Verify setup
./verify-setup.sh
```

### Testing
```bash
# Run unit tests
pytest zeus-aks-integration/tests/ -v

# Run with coverage
pytest --cov=zeus_aks_integration --cov-report=html

# Test specific components
pytest -k "test_processing" -v
```

## 📋 Coding Standards

### Python Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable and function names
- Include docstrings for all public functions

### Documentation
- Update README.md for user-facing changes
- Update relevant documentation in `docs/`
- Include inline comments for complex logic
- Use clear, concise language

### Commit Messages
Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add video processing status endpoint
fix(k8s): resolve namespace deployment issue
docs(readme): update deployment instructions
```

## 🧪 Testing Guidelines

### Unit Tests
- Write tests for all new functionality
- Maintain >90% code coverage
- Use descriptive test names
- Include both positive and negative test cases

### Integration Tests
- Test end-to-end workflows
- Test Azure service integration
- Test Kubernetes deployment scenarios

### Manual Testing
Before submitting a PR:
1. Run `./verify-setup.sh`
2. Run `./verify-credentials.sh` (if applicable)
3. Test Docker build: `docker build -t zeus-test .`
4. Test local API: `cd zeus-web-ui/api && python main.py`

## 🏗️ Architecture Guidelines

### Adding New Features
1. Follow existing patterns and conventions
2. Maintain separation of concerns
3. Use dependency injection where appropriate
4. Consider scalability and performance implications

### Kubernetes Changes
- Test manifests with `kubectl apply --dry-run=client`
- Follow Kubernetes best practices
- Consider security implications
- Update RBAC permissions as needed

### Azure Integration
- Use managed identities when possible
- Follow least-privilege principles
- Handle Azure API rate limits
- Include proper error handling and retries

## 🔒 Security Guidelines

### Code Security
- Never commit credentials or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security guidelines

### Infrastructure Security
- Use non-root containers
- Implement proper RBAC
- Use read-only filesystems where possible
- Regular security updates

## 📖 Documentation Standards

### Code Documentation
- Include docstrings for all public functions
- Document complex algorithms and business logic
- Keep comments up-to-date with code changes

### User Documentation
- Provide step-by-step instructions
- Include troubleshooting sections
- Use clear, non-technical language where appropriate
- Include examples and screenshots

## 🚀 Release Process

### Version Numbering
We follow Semantic Versioning (SemVer):
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Security review completed

## 🆘 Getting Help

### Community Support
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and general discussion

### Development Questions
- Check existing documentation first
- Search closed issues and pull requests
- Create a new issue with the "question" label

## 📜 Code of Conduct

### Our Standards
- Be respectful and inclusive
- Provide constructive feedback
- Focus on the issue, not the person
- Help create a welcoming environment for all contributors

### Unacceptable Behavior
- Harassment or discrimination
- Trolling or inflammatory comments
- Personal attacks
- Publishing private information without permission

## 🎉 Recognition

Contributors are recognized in several ways:
- Listed in the project's contributors
- Mentioned in release notes for significant contributions
- Special recognition for major features or fixes

Thank you for contributing to making video content more accessible for everyone! 🌟
