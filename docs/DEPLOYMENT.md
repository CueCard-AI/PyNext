# Deployment Guide

This guide covers deploying PyNext applications to production environments.

## Table of Contents

- [Production Build](#production-build)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Environment Variables](#environment-variables)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Health Checks](#health-checks)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Production Build

### Building for Production

```bash
# Create production build
pynext build

# With optimizations
pynext build --minify --no-sourcemap
```

### Build Output

```
.pynext/build/
├── pages/              # Compiled pages
├── static/             # Static assets
├── _pynext/            # Framework runtime
│   ├── runtime.js      # Hydration code
│   └── bundles/        # NPM bundles
├── manifest.json       # Build manifest
└── routes.json         # Route manifest
```

### Pre-deployment Checklist

```bash
# 1. Run tests
pytest tests/

# 2. Check for lint errors
ruff check .

# 3. Build for production
pynext build

# 4. Test production build locally
pynext start

# 5. Verify environment variables
cat .env.production
```

---

## Docker Deployment

### Basic Dockerfile

```dockerfile
# Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Node.js for npm packages
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build the application
RUN pynext build

# Expose port
EXPOSE 3000

# Run production server
CMD ["pynext", "start", "--host", "0.0.0.0", "--port", "3000"]
```

### Multi-Stage Build (Optimized)

```dockerfile
# Dockerfile

# ============================================
# Stage 1: Build
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Build for production
RUN pynext build

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/pynext /usr/local/bin/pynext

# Copy built application
COPY --from=builder /app/.pynext/build ./.pynext/build
COPY --from=builder /app/pynext.config.py .
COPY --from=builder /app/pages ./pages
COPY --from=builder /app/components ./components
COPY --from=builder /app/static ./static

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/_pynext/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "pynext.server:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:3000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - PYNEXT_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/_pynext/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  # Optional: PostgreSQL database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### Docker Build Commands

```bash
# Build image
docker build -t my-pynext-app .

# Run container
docker run -p 3000:3000 --env-file .env.production my-pynext-app

# Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Scale workers
docker-compose up -d --scale app=3
```

---

## Cloud Platforms

### Render

```yaml
# render.yaml

services:
  - type: web
    name: pynext-app
    env: python
    buildCommand: pip install -r requirements.txt && pynext build
    startCommand: gunicorn pynext.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
    envVars:
      - key: PYNEXT_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
    healthCheckPath: /_pynext/health
    autoDeploy: true
```

### Railway

```toml
# railway.toml

[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn pynext.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT"
healthcheckPath = "/_pynext/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 5
```

```json
// railway.json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "pynext start --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/_pynext/health"
  }
}
```

### Fly.io

```toml
# fly.toml

app = "my-pynext-app"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PYNEXT_ENV = "production"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "connections"
    hard_limit = 100
    soft_limit = 80

[[services]]
  protocol = "tcp"
  internal_port = 8080

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = "10s"
    timeout = "2s"
    path = "/_pynext/health"
```

```bash
# Deploy to Fly.io
fly launch
fly deploy
fly scale count 2  # Scale to 2 instances
```

### AWS (ECS/Fargate)

```yaml
# task-definition.json (simplified)

{
  "family": "pynext-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "pynext-app",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/pynext-app:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "PYNEXT_ENV", "value": "production"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/_pynext/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pynext-app",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```yaml
# cloudbuild.yaml

steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/pynext-app:$COMMIT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/pynext-app:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pynext-app'
      - '--image=gcr.io/$PROJECT_ID/pynext-app:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--memory=512Mi'
      - '--cpu=1'
      - '--min-instances=1'
      - '--max-instances=10'
      - '--set-env-vars=PYNEXT_ENV=production'

images:
  - 'gcr.io/$PROJECT_ID/pynext-app:$COMMIT_SHA'
```

### Heroku

```
# Procfile

web: gunicorn pynext.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

```bash
# runtime.txt
python-3.11.0
```

```bash
# Deploy to Heroku
heroku create my-pynext-app
heroku config:set PYNEXT_ENV=production
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
git push heroku main
```

---

## Reverse Proxy Setup

### Nginx

```nginx
# /etc/nginx/sites-available/pynext

upstream pynext_backend {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 80;
    server_name example.com www.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Static files (serve directly)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # NPM bundles
    location /_pynext/npm/ {
        alias /app/.pynext/bundles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://pynext_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /_pynext/health {
        proxy_pass http://pynext_backend;
        access_log off;
    }
}
```

### Caddy

```
# Caddyfile

example.com {
    # Automatic HTTPS with Let's Encrypt
    
    # Static files
    handle /static/* {
        root * /app
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }

    # NPM bundles
    handle /_pynext/npm/* {
        root * /app/.pynext/bundles
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }

    # Reverse proxy to application
    handle {
        reverse_proxy localhost:3000 {
            header_up X-Forwarded-Proto {scheme}
            header_up X-Real-IP {remote_host}
        }
    }

    # Compression
    encode gzip

    # Security headers
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}
```

---

## Environment Variables

### Production Environment File

```bash
# .env.production

# Application
PYNEXT_ENV=production
PYNEXT_DEBUG=false
SECRET_KEY=your-very-secure-secret-key-here

# Server
PYNEXT_HOST=0.0.0.0
PYNEXT_PORT=3000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
STRIPE_SECRET_KEY=sk_live_xxx
SENDGRID_API_KEY=SG.xxx

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx

# Feature flags
ENABLE_ANALYTICS=true
```

### Loading in Config

```python
# pynext.config.py

import os
from dotenv import load_dotenv

# Load environment-specific .env file
env = os.getenv("PYNEXT_ENV", "development")
load_dotenv(f".env.{env}")
load_dotenv(".env.local", override=True)

# Configuration
host = os.getenv("PYNEXT_HOST", "localhost")
port = int(os.getenv("PYNEXT_PORT", 3000))
debug = os.getenv("PYNEXT_DEBUG", "true").lower() == "true"
secret_key = os.getenv("SECRET_KEY")

# Validate required variables
if env == "production" and not secret_key:
    raise ValueError("SECRET_KEY is required in production")
```

### Secrets Management

```bash
# Never commit secrets to git!
echo ".env.production" >> .gitignore
echo ".env.local" >> .gitignore

# Use secrets manager in production
# AWS Secrets Manager
# Google Secret Manager
# HashiCorp Vault
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal (cron)
0 0 1 * * /usr/bin/certbot renew --quiet
```

### Direct SSL in PyNext

```python
# pynext.config.py

import os

ssl_enabled = True
ssl_cert = os.getenv("SSL_CERT_PATH", "/etc/letsencrypt/live/example.com/fullchain.pem")
ssl_key = os.getenv("SSL_KEY_PATH", "/etc/letsencrypt/live/example.com/privkey.pem")
```

```bash
# Start with SSL
pynext start --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem
```

---

## Health Checks

### Built-in Health Endpoint

PyNext provides a health check endpoint at `/_pynext/health`:

```bash
curl http://localhost:3000/_pynext/health
# {"status": "healthy", "timestamp": "2024-03-15T10:30:00Z"}
```

### Custom Health Check

```python
# pages/api/health.py

from pynext import api_route
from pynext.server import JSONResponse
import asyncpg

@api_route(methods=["GET"])
async def health(request):
    checks = {
        "status": "healthy",
        "checks": {}
    }
    
    # Database check
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        await conn.fetchval("SELECT 1")
        await conn.close()
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {e}"
        checks["status"] = "degraded"
    
    # Redis check
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        checks["checks"]["redis"] = "healthy"
    except Exception as e:
        checks["checks"]["redis"] = f"unhealthy: {e}"
        checks["status"] = "degraded"
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(checks, status_code=status_code)
```

### Kubernetes Probes

```yaml
# kubernetes deployment
spec:
  containers:
    - name: pynext-app
      livenessProbe:
        httpGet:
          path: /_pynext/health
          port: 3000
        initialDelaySeconds: 10
        periodSeconds: 30
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /_pynext/health
          port: 3000
        initialDelaySeconds: 5
        periodSeconds: 10
        timeoutSeconds: 3
        failureThreshold: 3
```

---

## Scaling Strategies

### Horizontal Scaling

```yaml
# Docker Compose scaling
docker-compose up -d --scale app=4

# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pynext-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pynext-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Vertical Scaling

```python
# pynext.config.py

import os

# Scale workers based on CPU
workers = (os.cpu_count() or 1) * 2 + 1
```

### Load Balancing

```nginx
# Nginx load balancing
upstream pynext_backend {
    least_conn;  # Least connections algorithm
    server 127.0.0.1:3001 weight=3;
    server 127.0.0.1:3002 weight=2;
    server 127.0.0.1:3003 weight=1;
    keepalive 32;
}
```

### Caching

```python
# pynext.config.py

# Redis caching
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Page caching
cache_pages = True
cache_ttl = 300  # 5 minutes
```

---

## Monitoring

### Logging

```python
# pynext.config.py

import logging

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=getattr(logging, log_level),
    format=log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
```

### Sentry Integration

```python
# pynext.config.py

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("PYNEXT_ENV"),
    traces_sample_rate=0.1,
)

# Add middleware
middleware = [
    SentryAsgiMiddleware,
]
```

### Prometheus Metrics

```python
# middleware/metrics.py

from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
import time

REQUEST_COUNT = Counter(
    'pynext_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'pynext_request_latency_seconds',
    'Request latency',
    ['method', 'endpoint']
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check logs
docker logs pynext-app

# Verify environment
docker exec pynext-app env | grep PYNEXT

# Test health endpoint
curl -v http://localhost:3000/_pynext/health
```

#### High Memory Usage

```bash
# Check memory
docker stats pynext-app

# Reduce workers
pynext start --workers 2

# Add memory limits
docker run -m 512m pynext-app
```

#### Slow Response Times

```bash
# Enable profiling
PYNEXT_PROFILE=true pynext start

# Check database queries
# Add query logging in development

# Check bundle sizes
pynext build --analyze
```

#### SSL Certificate Issues

```bash
# Test SSL
openssl s_client -connect example.com:443

# Check certificate expiry
openssl x509 -enddate -noout -in /path/to/cert.pem

# Renew certificate
certbot renew
```

### Debug Mode in Production

```bash
# NEVER enable debug in production
# But for temporary debugging:
PYNEXT_DEBUG=true pynext start

# Check specific endpoint
curl -v http://localhost:3000/problematic-route

# Tail logs
tail -f logs/app.log
```

---

## Deployment Checklist

```markdown
## Pre-Deployment

- [ ] All tests passing
- [ ] No lint errors
- [ ] Environment variables configured
- [ ] Secrets not in git
- [ ] Database migrations applied
- [ ] Static assets optimized

## Deployment

- [ ] Production build successful
- [ ] Docker image built and tested
- [ ] Health checks configured
- [ ] SSL certificates valid
- [ ] Logging configured
- [ ] Monitoring set up

## Post-Deployment

- [ ] Health endpoint responding
- [ ] Application accessible
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Alerts configured
- [ ] Backup verified
```

---

## Next Steps

- [Configuration](CONFIGURATION.md) - Production configuration
- [CLI Reference](CLI.md) - Build and start commands
- [Testing](TESTING.md) - Pre-deployment testing

