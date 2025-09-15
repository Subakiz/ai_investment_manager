# Production Secret Management Strategy

## Overview

This document outlines the strategy for managing secrets in the production deployment of the AI Investment Manager application, moving away from the local `.env` file approach used in development.

## Development vs Production

### Development (Current)
- Uses `.env` file loaded by `python-dotenv`
- Secrets stored in plain text locally
- Suitable for local development only

### Production (Recommended)
- Environment variables injected by deployment environment
- No `.env` file in container
- Secrets managed by external systems

## Production Secret Management Options

### 1. Container Orchestration Secrets (Recommended)

#### Docker Swarm Secrets
```bash
# Create secrets
echo "your_api_key_here" | docker secret create news_api_key -
echo "your_gemini_key_here" | docker secret create gemini_api_key -

# Update docker-compose.yml
services:
  web:
    secrets:
      - news_api_key
      - gemini_api_key
    environment:
      - NEWS_API_KEY_FILE=/run/secrets/news_api_key
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key

secrets:
  news_api_key:
    external: true
  gemini_api_key:
    external: true
```

#### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  NEWS_API_KEY: "your_api_key_here"
  GEMINI_API_KEY: "your_gemini_key_here"
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: web
        env:
        - name: NEWS_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: NEWS_API_KEY
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: GEMINI_API_KEY
```

### 2. Cloud Provider Secret Management

#### AWS Secrets Manager
```bash
# Store secrets
aws secretsmanager create-secret --name "ai-investment-manager/news-api-key" --secret-string "your_api_key_here"
aws secretsmanager create-secret --name "ai-investment-manager/gemini-api-key" --secret-string "your_gemini_key_here"

# Use AWS CLI or SDK to retrieve in application startup
```

#### Azure Key Vault
```bash
# Store secrets
az keyvault secret set --vault-name "ai-investment-kv" --name "news-api-key" --value "your_api_key_here"
az keyvault secret set --vault-name "ai-investment-kv" --name "gemini-api-key" --value "your_gemini_key_here"
```

#### Google Secret Manager
```bash
# Store secrets
gcloud secrets create news-api-key --data-file=-
gcloud secrets create gemini-api-key --data-file=-
```

### 3. HashiCorp Vault
```bash
# Store secrets
vault kv put secret/ai-investment-manager NEWS_API_KEY="your_api_key_here" GEMINI_API_KEY="your_gemini_key_here"

# Use Vault agent or API to retrieve
```

## Recommended Implementation

### For Simple Deployments (Docker Compose)

1. **Environment Variable Injection**
   ```bash
   # Set environment variables on the host
   export NEWS_API_KEY="your_actual_api_key"
   export GEMINI_API_KEY="your_actual_gemini_key"
   
   # Run docker-compose
   docker-compose up -d
   ```

2. **Environment File (Host-only)**
   ```bash
   # Create /etc/ai-investment-manager/.env on host
   NEWS_API_KEY=your_actual_api_key
   GEMINI_API_KEY=your_actual_gemini_key
   
   # Update docker-compose.yml
   env_file:
     - /etc/ai-investment-manager/.env
   ```

### For Production Deployments

1. **Use CI/CD Pipeline Secrets**
   - Store secrets in GitHub Secrets, GitLab Variables, etc.
   - Inject during deployment

2. **Application Code Modifications**
   ```python
   # Update src/config/settings.py
   import os
   from pathlib import Path
   
   class Config:
       def __init__(self):
           # Try to read from file (Docker secrets)
           if Path("/run/secrets/news_api_key").exists():
               with open("/run/secrets/news_api_key") as f:
                   self.NEWS_API_KEY = f.read().strip()
           else:
               self.NEWS_API_KEY = os.getenv("NEWS_API_KEY")
   ```

## Security Best Practices

1. **Never commit secrets to version control**
2. **Use least privilege access**
3. **Rotate secrets regularly**
4. **Monitor secret access**
5. **Use encryption at rest and in transit**
6. **Audit secret usage**

## Migration Steps

1. **Update application configuration**
   - Remove dependency on `.env` file in production
   - Add support for multiple secret sources

2. **Update deployment configuration**
   - Remove `.env` file from Docker image
   - Configure external secret injection

3. **Test secret injection**
   - Verify application starts without `.env`
   - Validate API functionality with injected secrets

4. **Deploy to production**
   - Set up secret management system
   - Deploy application with external secrets

## Current Production Docker Compose

The updated `docker-compose.yml` includes commented examples for secret injection:

```yaml
environment:
  # These should be injected by the deployment environment
  # - NEWS_API_KEY=${NEWS_API_KEY}
  # - GEMINI_API_KEY=${GEMINI_API_KEY}
```

To activate, uncomment and set environment variables on the host or use a secret management system.