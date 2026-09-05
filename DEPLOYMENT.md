# Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] `.env` file is in `.gitignore` (never commit secrets)
- [ ] API keys and connection strings configured in production environment
- [ ] Database migrations run successfully
- [ ] CORS origins restricted (not `["*"]`)
- [ ] Authentication/API keys configured
- [ ] Rate limiting enabled
- [ ] SSL/TLS certificates configured
- [ ] Logging and monitoring set up
- [ ] Backup strategy in place

---

## Environment Setup

### Production `.env`

Create `.env` in production with:

```bash
# API
API_PORT=8000
API_HOST=0.0.0.0

# Database (use managed service like Neon)
DATABASE_URL=postgresql://prod_user:STRONG_PASSWORD@ep-xxx.neon.tech/prod_db?sslmode=require

# LLM Judge
JUDGE_MODEL=claude-3-opus
OPENAI_API_KEY=sk-prod-...

# Trust Weights
TRUST_WEIGHT_W1=0.3
TRUST_WEIGHT_W2=0.4
TRUST_WEIGHT_W3=0.3

# Thresholds
GAMMA_THRESHOLD=0.5
GAMMA_CRITICAL=0.8

# Logging
LOG_LEVEL=WARNING

# Security
ALLOWED_ORIGINS=https://yourdomain.com,https://dashboard.yourdomain.com
API_RATE_LIMIT=100  # requests per minute
```

---

## Docker Deployment

### Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY api-and-sdk/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set working directory
WORKDIR /app/api-and-sdk

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run API
CMD ["python", "run_api.py"]
```

Build and run:

```bash
docker build -t legal-hallucination-api:latest .
docker run -p 8000:8000 --env-file .env legal-hallucination-api:latest
```

### Docker Compose (Full Stack)

```yaml
version: '3.9'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JUDGE_MODEL=${JUDGE_MODEL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_USER=halo_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=hallucination_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  dashboard:
    build: ./dashboard-and-eval/dashboard
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
```

Run with:

```bash
docker-compose up -d
```

---

## Cloud Deployment

### AWS ECS

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name legal-hallucination-api
   ```

2. **Push image:**
   ```bash
   docker tag legal-hallucination-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/legal-hallucination-api:latest
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/legal-hallucination-api:latest
   ```

3. **Create ECS task definition** (use CloudFormation or AWS Console)
   - Image: ECR URI
   - Memory: 512MB
   - CPU: 256
   - Port: 8000

4. **Create ECS service** with:
   - Task definition
   - Load balancer (ALB)
   - Auto-scaling (min 2, max 10 instances)

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/legal-hallucination-api
gcloud run deploy legal-hallucination-api \
  --image gcr.io/PROJECT-ID/legal-hallucination-api \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars DATABASE_URL=...,JUDGE_MODEL=... \
  --allow-unauthenticated
```

### Heroku

```bash
# Create app
heroku create legal-hallucination-api

# Set environment variables
heroku config:set DATABASE_URL=... JUDGE_MODEL=...

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

---

## Database Setup

### Neon PostgreSQL

1. **Create account:** https://console.neon.tech
2. **Create project** and database
3. **Get connection string:** Copy from project settings
4. **Set DATABASE_URL:**
   ```bash
   export DATABASE_URL="postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require"
   ```

### Initialize Database

```bash
# Run migrations
python -m api.analytics.init_db

# Build vector index (one-time)
python -m api.kb.build_index
```

---

## Security

### CORS Configuration

```python
# In api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://dashboard.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### API Key Authentication

```python
# In api/routes/check.py
from fastapi import Header, HTTPException

@app.post("/api/check")
async def check_hallucination(
    request: CheckRequest,
    x_api_key: str = Header(None),
    background_tasks: BackgroundTasks,
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ... rest of endpoint
```

### Rate Limiting

```python
# Install: pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/check")
@limiter.limit("100/minute")
async def check_hallucination(request: CheckRequest):
    # ...
```

### HTTPS/TLS

- Use reverse proxy (nginx, CloudFront) with SSL certificates
- Redirect HTTP → HTTPS
- Use HSTS header: `Strict-Transport-Security: max-age=31536000`

---

## Monitoring & Logging

### Logging

```python
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("API started")
logger.error("Pipeline failed: %s", str(e))
```

### Metrics

Track with Prometheus/Grafana:
- Request count and latency (by endpoint)
- Pipeline stage timings
- Error rates
- Database query time
- Trust_index distribution

### Alerting

Set up alerts for:
- API response time > 1s
- Error rate > 5%
- Database connection failures
- API key exhaustion (rate limiting)

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Daily backup with Neon (automatic)
# Or manual:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore:
psql $DATABASE_URL < backup_20260905.sql
```

### Vector Index Backup

```bash
# Backup FAISS index
tar -czf index_backup_$(date +%Y%m%d).tar.gz api/kb/index/

# Restore:
tar -xzf index_backup_20260905.tar.gz

# Or rebuild from database:
python -m api.kb.build_index
```

### Disaster Recovery Plan

1. **Database loss:** Restore from latest backup, rebuild vector index
2. **Vector index loss:** Rebuild from database (takes ~2 minutes)
3. **Full system loss:** Redeploy Docker image, restore database, rebuild index

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes (usually already created)
CREATE INDEX idx_created_at ON check_logs(created_at DESC);
CREATE INDEX idx_decision ON check_logs(decision);

-- Connection pooling (PgBouncer)
-- Configure in app: engine = create_engine(..., pool_pre_ping=True)
```

### Caching

```python
# Cache KB responses (e.g., statute text doesn't change often)
from functools import lru_cache

@lru_cache(maxsize=1000)
def lookup_section_cached(section_ref: str, act_name: str):
    return kb.lookup_section(section_ref, act_name)

# Cache OpenAI responses
# Store in Redis or PostgreSQL with TTL
```

### Async/Concurrency

- FastAPI handles async naturally
- Use `asyncio` for I/O-bound tasks
- Consider Celery for CPU-bound pipeline work

---

## Scaling

### Horizontal Scaling

```
Load Balancer
├─ API Instance 1
├─ API Instance 2
├─ API Instance 3
└─ API Instance N
    ↓
Shared PostgreSQL (read replicas)
Shared FAISS Index (cached in memory)
```

### Vertical Scaling

- Increase container CPU: 256 → 512 → 1024 vCPU
- Increase container memory: 512MB → 1GB → 2GB
- Add read replicas to PostgreSQL

### Caching Layer

- Redis for session cache, KB responses
- CloudFront for static assets (dashboard)
- In-memory FAISS index cache

---

## Rollback Plan

```bash
# If deployment fails, rollback to previous version:
docker pull legal-hallucination-api:v0.1.0
docker-compose up -d

# Or for cloud:
aws ecs update-service --cluster prod --service api --force-new-deployment --previous-version
```

---

## Post-Deployment

1. **Verify health:**
   ```bash
   curl https://api.yourdomain.com/health
   ```

2. **Test endpoints:**
   ```bash
   curl -X POST https://api.yourdomain.com/api/check \
     -H "Content-Type: application/json" \
     -d '{"text": "Section 43A..."}'
   ```

3. **Monitor logs:**
   ```bash
   # Docker
   docker logs -f legal-hallucination-api
   
   # Cloud Run
   gcloud run logs read legal-hallucination-api
   
   # ECS
   aws logs tail /ecs/legal-hallucination-api --follow
   ```

4. **Check metrics:**
   - API response time
   - Error rates
   - Database connections
   - Trust_index distribution

5. **User communication:**
   - Announce service availability
   - Share API documentation
   - Provide example requests

