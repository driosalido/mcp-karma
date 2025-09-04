# Docker Hub Setup for GitHub Actions

To enable automatic Docker image publishing, you need to set up Docker Hub credentials in your GitHub repository.

## Required Secrets

Add these secrets to your GitHub repository (`Settings > Secrets and variables > Actions`):

### 1. DOCKERHUB_USERNAME
Your Docker Hub username: `driosalido`

### 2. DOCKERHUB_TOKEN
A Docker Hub Personal Access Token (not your password):

1. Go to [Docker Hub Account Settings](https://hub.docker.com/settings/security)
2. Click "New Access Token"
3. Enter a description (e.g., "GitHub Actions mcp-karma")
4. Select permissions: "Public Repo Read, Write, Delete"
5. Copy the generated token
6. Add it as `DOCKERHUB_TOKEN` secret in GitHub

## How it Works

The GitHub Action will:
- Trigger on every new release
- Build multi-platform images (linux/amd64, linux/arm64)
- Tag images with:
  - The release tag (e.g., `v1.0.0`)
  - Semantic version variants (`1.0.0`, `1.0`, `1`)
  - `latest` tag
- Push to `driosalido/karma-mcp` on Docker Hub
- Update the repository description automatically

## Creating a Release

To trigger the workflow:
1. Go to GitHub repository > Releases
2. Click "Create a new release"
3. Create a new tag (e.g., `v1.0.0`)
4. Fill in release title and description
5. Click "Publish release"

The Docker image will be available at: `docker pull driosalido/karma-mcp:latest`
