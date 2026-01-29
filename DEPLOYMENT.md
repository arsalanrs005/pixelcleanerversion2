# Deployment Guide for Pixel Cleaner on Render

## Prerequisites

- A GitHub account
- Your code pushed to a GitHub repository
- A Render account (free tier works!)

## Step-by-Step Deployment Instructions

### 1. Prepare Your Repository

Make sure all your files are committed and pushed to GitHub:

```bash
# Check current status
git status

# If you have uncommitted changes, commit them
git add .
git commit -m "Ready for deployment"

# Push to GitHub
git push origin main
```

### 2. Sign Up / Log In to Render

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up using GitHub (recommended) or email
4. Verify your email if needed

### 3. Create a New Web Service

#### Method A: Using Render Dashboard (Manual Configuration)

1. **Navigate to Dashboard**:
   - After logging in, you'll see your dashboard
   - Click the "New +" button in the top right
   - Select "Web Service"

2. **Connect Your Repository**:
   - If not connected, click "Connect account" next to GitHub
   - Authorize Render to access your repositories
   - Select your repository: `pixelcleanerac` (or your repo name)
   - Click "Connect"

3. **Configure Your Service**:
   
   **Basic Settings:**
   - **Name**: `pixelcleaner` (or any name you prefer)
   - **Region**: Choose the closest region to your users (e.g., `Oregon (US West)`)
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (unless your app is in a subdirectory)

   **Build & Deploy:**
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

   **Plan:**
   - **Free**: Free tier (spins down after 15 min inactivity)
   - **Starter**: $7/month (always on)

4. **Advanced Settings** (Optional):
   - **Environment Variables**: None needed for basic setup
   - **Health Check Path**: `/health` (optional, but recommended)

5. **Create Web Service**:
   - Click "Create Web Service" at the bottom
   - Render will start building and deploying your app

#### Method B: Using render.yaml (Automatic - Recommended)

Since you already have `render.yaml` in your repository, Render can auto-detect it:

1. **Navigate to Dashboard**:
   - Click "New +" → "Blueprint"

2. **Connect Repository**:
   - Select your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Review Configuration**:
   - Render will show you the configuration from `render.yaml`
   - Review and click "Apply"

4. **Deploy**:
   - Render will create the service automatically
   - The deployment will start immediately

### 4. Monitor Deployment

1. **Build Logs**:
   - You'll see real-time build logs
   - Watch for any errors during `pip install`
   - Build typically takes 2-5 minutes

2. **Deploy Logs**:
   - After build, deployment starts
   - You'll see startup logs
   - Look for: "Your service is live at https://..."

3. **Common Issues**:
   - **Build fails**: Check that all dependencies are in `requirements.txt`
   - **Start fails**: Verify `gunicorn` is installed and `startCommand` is correct
   - **Timeout**: Free tier has longer cold starts (30-60 seconds)

### 5. Access Your Deployed App

Once deployed, your app will be available at:
```
https://pixelcleaner.onrender.com
```
(Replace `pixelcleaner` with your service name)

### 6. Test Your Deployment

1. **Health Check**:
   ```bash
   curl https://pixelcleaner.onrender.com/health
   ```
   Should return: `{"status":"healthy"}`

2. **Web Interface**:
   - Open `https://pixelcleaner.onrender.com` in your browser
   - You should see the upload interface

3. **Test File Upload**:
   - Upload a test CSV file
   - Enter a custom filename (optional)
   - Process and download the cleaned file

## Important Notes

### Free Tier Limitations

- **Spins down after 15 minutes** of inactivity
- **Takes ~30 seconds** to wake up when accessed
- **512 MB RAM** limit
- **100 GB bandwidth** per month
- **No custom domains** (only `.onrender.com` subdomain)

### Upgrading to Starter Plan ($7/month)

If you need:
- Always-on service (no spin-down)
- Faster response times
- More resources
- Custom domains

Upgrade in Render dashboard → Your Service → Settings → Plan

### Environment Variables

Currently, no environment variables are required. If you need to add them later:

1. Go to your service in Render dashboard
2. Click "Environment" tab
3. Add key-value pairs
4. Redeploy (automatic)

### Updating Your App

1. **Make changes** to your code locally
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. **Render auto-deploys**: Render will automatically detect the push and redeploy

### Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Monitor CPU, memory, and request metrics
- **Alerts**: Set up email alerts for deployment failures

## Troubleshooting

### App Won't Start

1. Check logs in Render dashboard
2. Verify `gunicorn` is in `requirements.txt`
3. Ensure `startCommand` is `gunicorn app:app`
4. Check that `app.py` exists in root directory

### Build Fails

1. Check `requirements.txt` has all dependencies
2. Verify Python version in `runtime.txt` matches Render's support
3. Check build logs for specific error messages

### 500 Errors

1. Check application logs
2. Verify file upload size limits (Render has limits)
3. Check that `pixelcleaner.py` is executable and in the repo

### Slow Response Times

- Free tier has cold starts (30-60 seconds after inactivity)
- Consider upgrading to Starter plan for always-on service
- Optimize your code for faster processing

## File Structure Required

Make sure your repository has:
```
pixelcleanerac/
├── app.py                 # Flask application
├── pixelcleaner.py        # Main processing script
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version
├── render.yaml           # Render configuration (optional)
├── templates/
│   └── index.html        # Web interface
└── README.md             # Documentation
```

## Support

- **Render Docs**: https://render.com/docs
- **Render Support**: support@render.com
- **Community**: https://community.render.com

## Next Steps

After successful deployment:

1. ✅ Test the web interface
2. ✅ Share the URL with your team
3. ✅ Monitor usage and performance
4. ✅ Consider upgrading if needed
5. ✅ Set up custom domain (if on paid plan)

---

**Congratulations!** Your Pixel Cleaner is now live on Render! 🎉




