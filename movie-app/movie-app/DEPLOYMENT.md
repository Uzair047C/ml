# Deployment Guide for MLOps

## Phase 1: Local Docker (Recommended for practice)

### 1. Create Dockerfile

**backend/Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt

COPY . .

CMD ["python", "app.py"]
```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    volumes:
      - ./backend:/app
    command: python app.py
```

### 3. Run with Docker Compose

```bash
docker-compose up
# API will be at http://localhost:5000
```

## Phase 2: Deploy to Render (Recommended for beginners)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/movie-recommender.git
git push -u origin main
```

### Step 2: Connect to Render

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name**: movie-recommender-api
   - **Environment**: Docker
   - **Build Command**: Leave blank (uses Dockerfile)
   - **Start Command**: python backend/app.py
   - **Port**: 5000

5. Add environment variables if needed
6. Click "Deploy"

### Deploy Frontend

1. Go to "New +" → "Static Site"
2. Select repository
3. Configure:
   - **Build Command**: (leave blank, no build needed)
   - **Publish Directory**: frontend
4. Click "Deploy"

## Phase 3: GitHub Actions CI/CD

### Create .github/workflows/deploy.yml

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
      
      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl https://api.render.com/deploy/srv-XXXXXXXXXXXX?key=YYYY
```

## Phase 4: Cloud Deployment Options

| Platform | Cost | Ease | Best For |
|----------|------|------|----------|
| **Render** | Free tier available | ⭐⭐⭐ | Quick prototypes |
| **Railway** | Pay-as-you-go | ⭐⭐⭐ | Startups |
| **AWS EC2** | Free tier 12mo | ⭐⭐ | Production scale |
| **Google Cloud Run** | Per-request pricing | ⭐⭐ | Serverless |
| **DigitalOcean** | $5/month | ⭐⭐ | VPS control |
| **AWS Lambda** | Per request | ⭐ | Serverless event-driven |

### Recommended Path:
1. **Start**: Render (easiest)
2. **Learn**: DigitalOcean with Docker
3. **Scale**: AWS or Google Cloud

## Phase 5: Monitoring & Logging

### Add Application Monitoring

```python
# In backend/app.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    logger.info(f"Recommendation request: {request.json}")
    # ... rest of code
```

### Use External Monitoring (when deployed)

- **Sentry**: Error tracking
- **DataDog**: Full observability
- **New Relic**: Performance monitoring
- **StatPing**: Uptime monitoring

## Model Versioning (MLOps Best Practice)

### Using MLflow (Optional but recommended)

```bash
pip install mlflow

# In training script:
import mlflow
mlflow.start_run()
mlflow.log_params({"max_features": 5000})
mlflow.sklearn.log_model(similarity_matrix, "recommendation_model")
mlflow.end_run()
```

### Using Git Tags for Versions

```bash
git tag -a v1.0.0 -m "Initial model release"
git push origin v1.0.0
```

## Data & Model Updates (MLOps Pipeline)

### Automated Retraining (Example Schedule)

```bash
# Use GitHub Actions scheduled workflow
# Retrain model weekly with new data

name: Weekly Model Retrain
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run training
        run: python backend/train_and_save_model.py
      - name: Commit new model
        run: |
          git add models/recommendation_model.pkl
          git commit -m "Auto: Updated model"
          git push
```

---

## Quick Local + Docker Workflow for Practice

```bash
# 1. Conda for local development
conda activate movie-recommender

# 2. Test locally
python backend/app.py

# 3. Build Docker image
docker build -t movie-rec-api backend/

# 4. Run Docker container
docker run -p 5000:5000 movie-rec-api

# 5. Or use Docker Compose (easier)
docker-compose up

# 6. Test API
curl http://localhost:5000/health
```

This gives you experience with:
- ✅ Containerization (Docker)
- ✅ Orchestration (Docker Compose)
- ✅ CI/CD (GitHub Actions)
- ✅ Cloud Deployment
- ✅ Model Versioning
- ✅ Monitoring
