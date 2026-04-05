# Contributing to MyPage48

First off, thank you for considering contributing to MyPage48! It's people like you that make MyPage48 such a great tool for the community.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for MyPage48. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related bugs.

Before creating bug reports, please check this list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible. Fill out [the required template](.github/ISSUE_TEMPLATE/bug_report.md), the information it asks for helps us resolve issues faster.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for MyPage48, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion and find related suggestions.

When you are creating an enhancement suggestion, please include as many details as possible. Fill out [the template](.github/ISSUE_TEMPLATE/feature_request.md), including the steps that you imagine you would take if the feature you're requesting existed.

### Your First Code Contribution

#### Local Setup

1. Fork the repository.
2. Clone your fork: `git clone https://github.com/your-username/mypage48.git`
3. Install dependencies:
   - Backend: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
4. Set up environment variables: `cp .env.example .env` and fill in the values.
5. Run the project: `sh scripts/start-all-dev.sh`

#### Pull Requests

The process which allows for a change to be submitted to the project:

1. Create a new branch: `git checkout -b feature/my-new-feature`
2. Make your changes and commit them: `git commit -m "feat: add some amazing feature"`
3. Push to the branch: `git push origin feature/my-new-feature`
4. Submit a Pull Request.

Please follow the [Pull Request Template](.github/pull_request_template.md) for your PR description.

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Code Style

* We use `flake8` for linting.
* Follow PEP 8 guidelines.

### Svelte/Frontend Style

* Use meaningful component names.
* Keep components small and focused.
* Use TailwindCSS for styling (if applicable) or Vanilla CSS as established in the project.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
