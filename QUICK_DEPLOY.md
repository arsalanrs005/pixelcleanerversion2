# Quick Deployment Checklist

## ✅ Pre-Deployment Checklist

- [ ] All code is committed to Git
- [ ] Code is pushed to GitHub
- [ ] `requirements.txt` includes Flask and gunicorn
- [ ] `render.yaml` exists (optional but recommended)
- [ ] `app.py` is in the root directory

## 🚀 Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Deploy on Render

**Option A: Auto-detect (Easiest)**
1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repo
4. Click "Apply" (uses `render.yaml` automatically)

**Option B: Manual Setup**
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click "Create Web Service"

### 3. Wait for Deployment
- Build: 2-5 minutes
- First access: May take 30-60 seconds (free tier cold start)

### 4. Test
Visit: `https://your-service-name.onrender.com`

## 📋 Configuration Summary

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Runtime | Python 3 |
| Health Check | `/health` (optional) |

## 🔗 Your App URL

After deployment, your app will be at:
```
https://[your-service-name].onrender.com
```

## ⚠️ Important Notes

- **Free tier**: Spins down after 15 min inactivity
- **Cold start**: 30-60 seconds on free tier
- **Auto-deploy**: Pushes to main branch trigger redeploy

## 🆘 Need Help?

See `DEPLOYMENT.md` for detailed instructions and troubleshooting.





