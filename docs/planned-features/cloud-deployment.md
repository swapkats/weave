# Cloud Deployment Guide

Practical guide to deploying Weave workflows to AWS, GCP, and Docker.

## Overview

Weave supports deployment to multiple cloud platforms:

- **AWS Lambda** - Serverless execution on AWS
- **GCP Cloud Functions** - Serverless execution on Google Cloud
- **Docker** - Containerized execution anywhere

All deployments use an **extensible provider system** that can be customized.

---

## Quick Start

### 1. Install with Deployment Support

```bash
# AWS
pip install weave-cli[aws]

# GCP
pip install weave-cli[gcp]

# Docker
pip install weave-cli[docker]

# All providers
pip install weave-cli[deploy]
```

### 2. Deploy Your Workflow

```bash
# AWS Lambda
weave deploy --name my-weave --provider aws --region us-east-1

# GCP Cloud Functions
weave deploy --name my-weave --provider gcp --region us-central1

# Docker
weave deploy --name my-weave --provider docker
```

---

## AWS Lambda Deployment

### Setup

```bash
# Install dependencies
pip install weave-cli[aws]

# Set credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### Deploy

```bash
weave deploy \
  --name my-weave-function \
  --provider aws \
  --type lambda \
  --region us-east-1
```

### What Happens

1. Creates deployment package with `.weave.yaml`
2. Creates IAM role for Lambda execution
3. Creates or updates Lambda function
4. Creates API Gateway endpoint
5. Returns deployment URL

### Invoke

```bash
curl -X POST https://your-endpoint.lambda-url.aws/ \
  -H "Content-Type: application/json" \
  -d '{"weave": "your_weave_name"}'
```

---

## GCP Cloud Functions Deployment

### Setup

```bash
# Install dependencies
pip install weave-cli[gcp]

# Authenticate with gcloud
gcloud auth login
gcloud config set project your-project-id

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GCP_PROJECT_ID="your-project"
```

### Deploy

```bash
weave deploy \
  --name my-weave-function \
  --provider gcp \
  --type function \
  --region us-central1
```

### Invoke

```bash
curl -X POST https://us-central1-project.cloudfunctions.net/my-weave \
  -H "Content-Type: application/json" \
  -d '{"weave": "your_weave_name"}'
```

---

## Docker Deployment

### Local Deployment

```bash
# Install dependencies
pip install weave-cli[docker]

# Deploy and run
weave deploy --name my-weave --provider docker
```

### Push to Registry

```bash
# Set registry credentials
export DOCKER_REGISTRY_URL="docker.io/username"
export DOCKER_USERNAME="username"
export DOCKER_PASSWORD="password"

# Build and push
weave deploy --name my-weave --provider docker --push-only
```

---

## Managing Deployments

### List All Deployments

```bash
weave deployments

# Filter by provider
weave deployments --provider aws
```

### Destroy Deployment

```bash
weave undeploy my-weave --provider aws

# Force without confirmation
weave undeploy my-weave --provider aws --force
```

---

## Configuration Reference

### Environment Variables

```yaml
deployment:
  env_vars:
    OPENAI_API_KEY: "${OPENAI_API_KEY}"
    ENVIRONMENT: "production"
```

### Resource Allocation

```yaml
deployment:
  memory_mb: 1024
  timeout_seconds: 300
```

### Authentication

```yaml
deployment:
  auth:
    method: env_vars  # or: api_key, service_account, iam_role
```

---

## Best Practices

1. **Test locally first** with Docker
2. **Use environment variables** for secrets
3. **Set appropriate timeouts** for LLM calls (300s+)
4. **Monitor costs** with provider dashboards
5. **Deploy to regions** close to users

---

## Troubleshooting

### AWS: boto3 not installed

```bash
pip install boto3
```

### GCP: gcloud not found

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
```

### Docker: Cannot connect to daemon

```bash
# Start Docker Desktop or
sudo systemctl start docker
```

---

## Next Steps

- [Full Deployment Guide](./deployment.md) - Complete configuration options
- [Real Execution](./real-execution.md) - Running with real LLMs
- [Observability](./observability-and-runtime.md) - Monitoring deployments
