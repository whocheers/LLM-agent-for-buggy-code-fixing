# GitHub Repository Setup

Follow these steps to create a GitHub repository for this project.

## Prerequisites

- GitHub account
- Git installed on your system
- Command-line access

## Step 1: Install Git (if needed)

### macOS
```bash
xcode-select --install
```

### Ubuntu/Debian
```bash
sudo apt-get install git
```

### Windows
Download from: https://git-scm.com/download/win

## Step 2: Initialize Local Repository

```bash
# Navigate to project directory
cd evaluation_of_agentic_system

# Initialize git repository
git init

# Configure git (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: LLM-based code fixing agent with HumanEvalFix evaluation"
```

## Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `code-fixing-agent`
3. Description: "LLM-based AI agent that fixes buggy Python code, evaluated on HumanEvalFix"
4. Choose: **Public** (recommended for sharing)
5. **Do NOT** initialize with README (we already have one)
6. Click "Create repository"

## Step 4: Connect Local to GitHub

After creating the repository, GitHub will show instructions. Follow the "push an existing repository" section:

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/code-fixing-agent.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 5: Verify Repository

1. Go to your repository URL: `https://github.com/YOUR_USERNAME/code-fixing-agent`
2. Check that all files are present
3. Verify that README.md displays correctly

## Step 6: Add Repository Description (Optional)

On your GitHub repository page:
1. Click the ⚙️ icon next to "About"
2. Add description: "LLM-based AI agent for fixing buggy Python code"
3. Add topics: `llm`, `code-generation`, `langgraph`, `python`, `bug-fixing`, `react-agent`
4. Save changes

## Repository Structure Check

Your repository should include:

```
✓ README.md
✓ QUICKSTART.md
✓ RESULTS_EXAMPLE.md
✓ LICENSE
✓ requirements.txt
✓ config.py
✓ main.py
✓ example_usage.py
✓ setup.sh
✓ .gitignore
✓ src/
  ✓ agent/
  ✓ evaluation/
  ✓ tools/
```

## Useful Git Commands

### After Making Changes

```bash
# Check status
git status

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push
```

### Viewing History

```bash
# View commit history
git log --oneline

# View changes
git diff
```

### Branching (Optional)

```bash
# Create new branch for experiments
git checkout -b experiment-branch

# Switch back to main
git checkout main

# Merge branch
git merge experiment-branch
```

## Making Repository More Visible

### Add Badges to README

Add at the top of README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)
```

### Add Screenshots

If you run the evaluation and get good results:
1. Take screenshots of the console output
2. Create an `images/` directory
3. Add images to repository
4. Reference in README.md

## Sharing Your Repository

Once pushed to GitHub, share the link:

```
https://github.com/YOUR_USERNAME/code-fixing-agent
```

For the JetBrains interview, you can share:
- Direct repository URL
- Link to README for overview
- Link to RESULTS_EXAMPLE.md for sample results

## Troubleshooting

### "Permission denied (publickey)"

Use HTTPS instead of SSH:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/code-fixing-agent.git
```

### "Repository not found"

Make sure:
1. Repository name matches exactly
2. You've created the repository on GitHub
3. Your GitHub username is correct in the URL

### Large Files Warning

If you get warnings about large files (model weights):
1. Models are downloaded to cache, not included in repository
2. `.gitignore` already excludes cache directories
3. Never commit files > 100MB to GitHub

## Next Steps

After setting up GitHub:

1. **Add a GitHub Actions workflow** (optional) for automated testing
2. **Create a release** with tagged version
3. **Write contributing guidelines** if accepting contributions
4. **Add documentation** for extending the agent

## Example GitHub Actions (Optional)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - run: pip install -r requirements.txt
    - run: python -m pytest tests/
```

This will automatically run tests on every push.
