# Pixel Cleaner

A Python script to clean and deduplicate CSV files, specifically designed for pixel export data. This script processes large CSV files efficiently and can be deployed on Render or similar platforms.

## Features

- **Deduplication**: Removes duplicate entries based on FIRST_NAME + LAST_NAME combination
- **Phone Cleaning**: Normalizes phone numbers and filters based on DNC (Do Not Contact) flags
- **Email Extraction**: Captures the first valid email address
- **DNC Filtering**: Keeps only phone numbers with DNC flag "N" (excluding "Y" flags)
- **Large File Support**: Efficiently processes large CSV files without loading everything into memory at once

## Requirements

- Python 3.7+
- Standard library only (no external dependencies required)

## Usage

### Command Line

```bash
python pixelcleaner.py <input_csv> <output_csv>
```

### Example

```bash
python pixelcleaner.py "pixel_export of fix&flow.csv" "cleaned_output.csv"
```

## How It Works

1. **Reads the input CSV** row by row
2. **Groups records** by FIRST_NAME + LAST_NAME (case-insensitive)
3. **Collects all phone numbers** from phone-related columns (DIRECT_NUMBER, MOBILE_PHONE, PERSONAL_PHONE, SKIPTRACE_WIRELESS_NUMBERS, etc.)
4. **Matches phones with DNC flags** from corresponding DNC columns
5. **Filters phones** to keep only those with DNC flag "N" (or empty/missing DNC flag)
6. **Deduplicates** phone numbers while preserving order
7. **Extracts first email** from email-related columns
8. **Outputs cleaned CSV** with:
   - PRIMARY_PHONE and PRIMARY_EMAIL
   - Additional phones in PHONE_1, PHONE_2, etc.
   - DNC flags in PHONE_DNC_1, PHONE_DNC_2, etc.
   - All other fields (excluding original DNC columns)

## Output Format

The cleaned CSV includes:

- `FIRST_NAME`, `LAST_NAME` - Person identifiers
- `PRIMARY_PHONE` - First phone number (filtered by DNC)
- `PRIMARY_EMAIL` - First email address
- `EMAIL_1`, `EMAIL_2`, etc. - Additional emails
- `PHONE_1`, `PHONE_2`, etc. - Additional phone numbers
- `PHONE_DNC_1`, `PHONE_DNC_2`, etc. - DNC flags for corresponding phones
- All other original fields (excluding original DNC columns)

## Deployment on Render

### Step-by-Step Guide

#### Option 1: Using Render Dashboard (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/pixelcleanerac.git
   git push -u origin main
   ```

2. **Go to Render Dashboard**:
   - Visit https://dashboard.render.com
   - Sign up or log in (you can use GitHub to sign in)

3. **Create a New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub account if not already connected
   - Select your repository (`pixelcleanerac`)

4. **Configure the service**:
   - **Name**: `pixelcleaner` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (or `.` if needed)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free tier is sufficient for testing

5. **Deploy**: Click "Create Web Service" - Render will automatically deploy your service

#### Option 2: Using render.yaml (Automatic)

If you have `render.yaml` in your repository (which you do!), Render will automatically detect it:

1. **Push your code to GitHub** (same as Option 1, step 1)

2. **Go to Render Dashboard**:
   - Visit https://dashboard.render.com
   - Click "New +" → "Blueprint"

3. **Connect Repository**:
   - Select your GitHub repository
   - Render will automatically read `render.yaml` and configure everything

4. **Deploy**: Click "Apply" - Render will create the service with the settings from `render.yaml`

### After Deployment

- Your app will be available at: `https://pixelcleaner.onrender.com` (or your custom name)
- First deployment may take 5-10 minutes
- Free tier services spin down after 15 minutes of inactivity (takes ~30 seconds to wake up)

### API Usage

Once deployed, you can use the API:

**Health Check:**
```bash
curl https://your-service.onrender.com/health
```

**Clean CSV:**
```bash
curl -X POST \
  -F "file=@your-input.csv" \
  https://your-service.onrender.com/clean \
  --output cleaned_output.csv
```

**Python Example:**
```python
import requests

url = "https://your-service.onrender.com/clean"
with open("input.csv", "rb") as f:
    response = requests.post(url, files={"file": f})
    with open("cleaned.csv", "wb") as out:
        out.write(response.content)
```

### Manual Deployment

Alternatively, you can deploy the script as a background service:
- Use the command: `python pixelcleaner.py input.csv output.csv`
- Configure as a Background Worker on Render

## Notes

- The script processes files in chunks to handle large files efficiently
- Phone numbers are normalized (removes formatting, handles country codes)
- Only phones with DNC flag "N" (or empty) are kept in the output
- Original DNC columns (DIRECT_NUMBER_DNC, MOBILE_PHONE_DNC, etc.) are removed from output

## Performance

- Processes ~1000 rows per second
- Memory efficient - doesn't load entire file into memory
- Suitable for files with hundreds of thousands of rows

