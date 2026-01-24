# Photometrics AI Website

Hugo static site for photometrics.ai marketing website.

## Tech Stack

- **Static Site Generator:** Hugo
- **Hosting:** AWS Amplify
- **Repository:** GitHub (Photometrics-ai/photometricsai-website)

## Development

```bash
# Run local dev server
hugo server -D

# Build for production
hugo --minify
```

## Deployment

Deployment is a **two-step process**:

### Step 1: Push to GitHub

```bash
git add <files>
git commit -m "Your commit message"
git push origin master
```

### Step 2: Trigger AWS Amplify Build

Amplify sometimes auto-detects pushes, but often needs manual trigger:

```bash
# Trigger deployment via AWS CLI
aws amplify start-job --app-id d22p16j9j2s18f --branch-name master --job-type RELEASE

# Check build status
aws amplify list-jobs --app-id d22p16j9j2s18f --branch-name master --max-results 1

# Get detailed job info
aws amplify get-job --app-id d22p16j9j2s18f --branch-name master --job-id <JOB_ID>
```

### Amplify App Details

- **App ID:** `d22p16j9j2s18f`
- **App Name:** `photometricsai-website`
- **Region:** `us-east-2`
- **Branch:** `master`
- **Console:** https://us-east-2.console.aws.amazon.com/amplify/home?region=us-east-2#/d22p16j9j2s18f

### Build Time

Typical build + deploy takes ~90 seconds.

### Troubleshooting

If site doesn't update after deploy:
1. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Check in incognito/private window
3. Verify build succeeded: `aws amplify list-jobs --app-id d22p16j9j2s18f --branch-name master --max-results 1`
