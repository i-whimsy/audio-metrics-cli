# PyPI Release Guide

## Prerequisites

1. **PyPI Account**: Create at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **twine**: `pip install twine`

## Release Steps

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.0"  # Update this
```

### 2. Build Package

```bash
cd audio-metrics-cli

# Install build tools
pip install build

# Build source and wheel
python -m build
```

This creates:
- `dist/audio_metrics_cli-0.1.0.tar.gz` (source distribution)
- `dist/audio_metrics_cli-0.1.0-py3-none-any.whl` (wheel)

### 3. Test on TestPyPI (Recommended)

```bash
# Install twine
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ audio-metrics-cli
```

### 4. Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

### 5. Verify

```bash
# Install from PyPI
pip install audio-metrics-cli

# Verify installation
audio-metrics --version
```

## GitHub Release

1. Go to https://github.com/i-whimsy/audio-metrics-cli/releases
2. Click "Create a new release"
3. Tag version: `v0.1.0`
4. Release title: `v0.1.0 - Initial Release`
5. Add release notes
6. Publish

## Automated Release (Optional)

Create `.github/workflows/release.yml`:

```yaml
name: Release to PyPI

on:
  release:
    types: [published]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install build
        run: pip install build
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

## Security Notes

- **Never commit API tokens** to git
- Store token in environment variable: `PYPI_API_TOKEN`
- Use `.pypirc` for local development (but don't commit it)

## Troubleshooting

### File already exists
```bash
# Increment version in pyproject.toml
# Rebuild and upload
```

### Invalid metadata
```bash
# Check pyproject.toml syntax
# Validate with: python -m build --no-isolation
```

### Authentication failed
```bash
# Check token is correct
# Use username: __token__
```
