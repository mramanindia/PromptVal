# Publishing PromptVal to PyPI

This guide explains how to publish the PromptVal package to PyPI so it can be installed with `pip install promptval`.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [Test PyPI](https://test.pypi.org/) (for testing)
   - [PyPI](https://pypi.org/) (for production)

2. **API Tokens**: Generate API tokens for both platforms:
   - Go to Account Settings → API tokens
   - Create a new token with appropriate scope
   - Save the tokens securely

## Step 1: Install Build Tools

```bash
# Install build tools
pip install build twine

# Verify installation
python -m build --version
twine --version
```

## Step 2: Update Package Metadata

The `pyproject.toml` has been updated with:
- ✅ Correct author information
- ✅ Proper description
- ✅ GitHub repository URLs
- ✅ Comprehensive classifiers
- ✅ All optional dependencies

## Step 3: Build the Package

```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Verify the build
ls dist/
# Should show: promptval-0.1.0-py3-none-any.whl and promptval-0.1.0.tar.gz
```

## Step 4: Test on Test PyPI

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ promptval

# Test the package
promptval --help
```

## Step 5: Publish to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Verify installation
pip install promptval

# Test the package
promptval --help
```

## Step 6: Update Documentation

After successful publishing, update the README.md to reflect PyPI availability:

```markdown
## 🚀 Installation

### From PyPI (Recommended)

```bash
# Basic installation
pip install promptval

# With specific provider support
pip install promptval[openai]        # OpenAI support
pip install promptval[anthropic]     # Anthropic support  
pip install promptval[gemini]        # Google Gemini support
pip install promptval[all]           # All providers

# For development
pip install promptval[dev]
```

### From Source (Development)

```bash
git clone https://github.com/mramanindia/PromptVal.git
cd PromptVal
pip install -e .
```
```

## Step 7: Create GitHub Release

1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v0.1.0`
4. Release title: `PromptVal v0.1.0`
5. Description: Copy from CHANGELOG or describe new features
6. Attach the built wheel file (`dist/promptval-0.1.0-py3-none-any.whl`)

## Step 8: Set up CI/CD (Optional)

Create `.github/workflows/publish.yml` for automated publishing:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Version Management

For future releases:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # or 0.2.0, 1.0.0, etc.
   ```

2. **Update changelog** in `CHANGELOG.md`

3. **Commit and tag**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

4. **Build and publish**:
   ```bash
   python -m build
   twine upload dist/*
   ```

## Troubleshooting

### Common Issues

**"Package already exists"**
- The package name `promptval` might be taken
- Check on PyPI: https://pypi.org/project/promptval/
- If taken, update `name` in `pyproject.toml`

**"Invalid credentials"**
- Check API token is correct
- Ensure token has proper scope (upload permissions)

**"Package not found after upload"**
- PyPI indexing can take a few minutes
- Check package page: https://pypi.org/project/promptval/

**"Version already exists"**
- Increment version number in `pyproject.toml`
- PyPI doesn't allow overwriting existing versions

### Verification Commands

```bash
# Check package info
pip show promptval

# Check available versions
pip index versions promptval

# Test installation
pip install promptval[openai]
promptval --help
```

## Security Notes

- Never commit API tokens to git
- Use environment variables for tokens
- Consider using `keyring` for secure token storage
- Enable 2FA on PyPI accounts

## Success Checklist

- [ ] Package builds without errors
- [ ] Uploads to Test PyPI successfully
- [ ] Installs from Test PyPI correctly
- [ ] Uploads to production PyPI successfully
- [ ] Installs from PyPI with `pip install promptval`
- [ ] All CLI commands work
- [ ] Documentation updated
- [ ] GitHub release created
- [ ] CI/CD pipeline set up (optional)

Once published, users will be able to install your package with:

```bash
pip install promptval
pip install promptval[openai]
```

And use it immediately:

```bash
promptval scan ./my_prompts
promptval prompt --text "Your prompt here"
```
