# GitHub Secrets Setup Instructions

Follow these steps to configure the required secrets for Docker Hub publishing.

## Step 1: Create Docker Hub Access Token

1. Go to [Docker Hub](https://hub.docker.com/) and log in
2. Click your profile picture → **Account Settings**
3. Go to **Security** tab
4. Click **New Access Token**
5. Fill in:
   - **Access Token Description**: `GitHub Actions mcp-karma`
   - **Access permissions**: Select **Public Repo Read, Write, Delete**
6. Click **Generate**
7. **IMPORTANT**: Copy the token immediately (you won't see it again)

## Step 2: Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/driosalido/mcp-karma`
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Add DOCKERHUB_USERNAME Secret
- **Name**: `DOCKERHUB_USERNAME`
- **Secret**: `driosalido`
- Click **Add secret**

### Add DOCKERHUB_TOKEN Secret
- **Name**: `DOCKERHUB_TOKEN`
- **Secret**: Paste the token you copied from Docker Hub
- Click **Add secret**

## Step 3: Verify Setup

After adding both secrets, you should see:
- ✅ `DOCKERHUB_USERNAME`
- ✅ `DOCKERHUB_TOKEN`

## Step 4: Test the Workflow

Create a release to test:
1. Go to **Releases** tab in your repository
2. Click **Create a new release**
3. **Choose a tag**: `v0.1.0` (create new tag)
4. **Release title**: `Initial Release`
5. **Description**: Add release notes
6. Click **Publish release**

The GitHub Action will automatically:
- Build the Docker image
- Push to `driosalido/karma-mcp:v0.1.0` and `driosalido/karma-mcp:latest`
- Update the Docker Hub repository description

## Troubleshooting

If the workflow fails:
- Check the **Actions** tab for error details
- Verify secrets are correctly named and contain valid values
- Ensure your Docker Hub account has permissions to create repositories