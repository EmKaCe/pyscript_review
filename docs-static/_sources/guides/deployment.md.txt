# Deployment Guide

This guide describes how to deploy the SciPro Review application.

## GitHub Pages Deployment

The application is a client-side SPA and is deployed to GitHub Pages for public access.

### Deployment Steps

1. **Build Assets**: Ensure all static assets (CSS, YAML data) are in the `static/` directory.
2. **Wheel Management**: Use the provided script to download required Python wheels for the PyScript runtime:
   ```bash
   uv run scripts/download_wheels.py
   ```
3. **Configure Runtime**: Update `pyscript.json` to include the necessary packages and local wheels.
4. **Push to GitHub**: Push the updated files to the `main` branch (or a dedicated `gh-pages` branch).

## Runtime Configuration

### pyscript.json

The `pyscript.json` file controls the Pyodide environment. Ensure it contains:
- `packages`: List of PyPI packages needed.
- `files`: List of local files and wheels to be loaded into the virtual filesystem.

### Static Assets

The following assets must be served along with the HTML:
- `theme.css`: The Tailwind v4 custom properties.
- `criteria.yaml`: The grading rubric data.
- `.whl` files: The pre-compiled dependencies for the browser.
