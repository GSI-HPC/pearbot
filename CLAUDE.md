# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pearbot is an AI-powered code review tool that analyzes Pull Requests on GitHub and local diffs using locally installed AI models. It uses a multi-agent architecture with reflection to provide comprehensive code reviews.

## Architecture

### Core Components

- **Agent System** (`src/agents.py`): Multi-agent architecture with two primary roles:
  - `code_reviewer`: Performs initial code analysis using configurable prompts
  - `feedback_improver`: Synthesizes multiple initial reviews into a final comprehensive review

- **Review Modes**:
  - **GitHub App Mode** (`src/review_github.py`): Flask webhook server that responds to `@pearbot review` comments
  - **Local Diff Mode** (`src/review_local.py`): Command-line analysis of git diffs or patch files

- **Model Integration** (`src/model.py`, `src/ollama_utils.py`):
  - Primary integration with Ollama for local AI models
  - Fallback to direct HTTP requests when needed
  - Model validation and availability checking

- **Prompt System** (`src/prompts.yaml`): Configurable prompt templates with multiple styles (`default`, `simple`)

### Key Workflows

1. **Multi-Agent Review Process**: Uses multiple models for initial reviews, then a final model to synthesize feedback
2. **GitHub Webhook Integration**: Authenticates via GitHub App, processes PR data, posts review comments
3. **Local Diff Analysis**: Reads from stdin or file, processes git patches/diffs directly

## Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install .

# Install test dependencies
pip install .[test]

# Install Ollama model (default: llama3.1)
ollama pull llama3.1
```

### Testing
```bash
# Run tests locally
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_basic.py
```

### Running the Application

Pearbot supports both execution methods for user convenience:

```bash
# Method 1: Direct script execution (simple and intuitive)
python src/pearbot.py --server
python src/pearbot.py --diff path/to/diff/file
git diff | python src/pearbot.py

# Method 2: Module execution (Python best practice)
python -m src.pearbot --server
python -m src.pearbot --diff path/to/diff/file
git diff | python -m src.pearbot

# Other examples (both methods work)
python src/pearbot.py --list-models
python src/pearbot.py --model llama3.1 --prompt-style simple --initial-review-models "llama3.1,llama3.1,llama3.1"
python src/pearbot.py --skip-reasoning

# Generate format-patch and analyze
git format-patch HEAD~3..HEAD --stdout | python src/pearbot.py
```

### Environment Configuration

Required for GitHub App mode (`.env` file):
```
GITHUB_APP_ID=your_github_app_id
GITHUB_PRIVATE_KEY=your_github_private_key
GITHUB_APP_WEBHOOK_SECRET=your_github_webhook_secret
```

## Key Implementation Details

- **Model Flexibility**: Supports different models for initial reviews vs final synthesis
- **Prompt Customization**: YAML-based prompt system with examples and multiple styles
- **Security**: Webhook signature verification, JWT authentication for GitHub API
- **Error Handling**: Graceful model validation, GitHub API error handling
- **Processing Options**: Can skip AI reasoning sections, use multiple review models

## File Structure Context

- `src/pearbot.py`: Main entry point with argument parsing
- `src/agents.py`: Core Agent class with prompt loading and model interaction
- `src/review_github.py`: GitHub webhook server and PR processing
- `src/review_local.py`: Local diff analysis functionality
- `src/prompts.yaml`: Configurable prompt templates and examples
- `src/ollama_utils.py`: Model validation and Ollama integration
- `src/utils.py`: Utility functions (e.g., reasoning removal)
- `src/storage.py`: Session management utilities

## Testing and Validation

The application validates available models before processing and provides clear error messages for missing dependencies or configuration issues.