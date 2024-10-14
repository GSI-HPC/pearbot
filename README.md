[![CI](https://github.com/rbx/pearbot/actions/workflows/ci.yml/badge.svg)](https://github.com/rbx/pearbot/actions/workflows/ci.yml)

# Pearbot

Pearbot is an AI assistant that reviews Pull Requests on GitHub and/or local diffs. It leverages locally installed AI models in a multi-agent setup with reflection to provide code reviews, helping improve their code quality and catch potential issues early in the development process.

## Prerequisites

- Python 3.9 or higher
- GitHub account (only for Pull Request reviews)
- Ollama or compatible AI model service

Install and run the Ollama AI model service by following the instructions in the [ollama website](https://ollama.com/download).

Install at least one model to use with Pearbot (default of pearbot is `llama3.1`):
```
ollama pull llama3.1
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/rbx/pearbot.git
   cd pearbot
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```
   pip install .
   ```

## Configuration (for use as GitHub App)

1. Create a `.env` file in the project root and add the following environment variables:
   ```
   GITHUB_APP_ID=your_github_app_id
   GITHUB_PRIVATE_KEY=your_github_private_key
   GITHUB_APP_WEBHOOK_SECRET=your_github_webhook_secret
   ```

2. Replace the placeholder values with your actual GitHub App credentials.

## Usage

### As a GitHub App

1. Set up your GitHub App and configure the webhook URL to point to your Pearbot instance.

2. Run the Pearbot server:
   ```
   python pearbot.py --server
   ```

3. The server will now listen for GitHub webhook events and automatically review Pull Requests when it encounters `@pearbot review` in a comment.

### For Local Diff Analysis

To analyze a local diff file:

```
python pearbot.py --diff path/to/your/diff/file
```

Or pipe a diff directly:

```
git diff | python pearbot.py
```

You can generate diffs that include commit messages, e.g.:
```
git format-patch HEAD~3..HEAD --stdout | python pearbot.py
```
