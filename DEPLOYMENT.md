# Deployment Process

This document explains the automated deployment process for the project. The publish process is triggered **automatically on version change** (i.e. when the version in `killercoda_cli/__about__.py` is updated) and runs on the `main` branch.

## What It Does

1. **Version Detection**  
   - The process reads the new version from `killercoda_cli/__about__.py` and sets it as the `PYPI_VERSION`.
   - A version change is considered the trigger for the publish process.

2. **Artifact Build & Upload**  
   - The `build` job creates source distributions (sdist) and wheel artifacts.
   - These artifacts are uploaded as GitHub build artifacts for later use.

3. **Artifact Download**  
   - In the `publish` job, the artifacts are downloaded using the `actions/download-artifact` action.
   
4. **Repository Checkout**  
   - The repository is checked out to ensure a proper Git context. This is crucial for generating changelogs, creating tags, and pushing them.

5. **Publish to PyPI**  
   - The downloaded artifacts are published to PyPI using the `pypa/gh-action-pypi-publish` action.
   - The process uses the PyPI API token from repository secrets to authenticate and perform the upload.

6. **Changelog Generation**  
   - The deployment step generates a changelog by inspecting Git commit history:
     - If no previous Git tags are found, it generates a changelog for **all commits**.
     - If a previous tag exists, it includes only commits since the last tag.
     
7. **Tag Creation & Release**  
   - A new Git tag (formatted as `v<version>`, e.g., `v1.2.3`) is created and pushed to the origin.
   - A GitHub release is created using this tag, and the generated changelog is attached as the release body.

## Trigger Conditions

- **Version Change:**  
  The publish process is triggered when there is a change in the version (in `killercoda_cli/__about__.py`).

- **Branch Restriction:**  
  The process runs on the `main` branch only.
