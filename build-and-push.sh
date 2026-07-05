#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT_ID="488850522194"
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "=== Logging in to ECR ==="
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_BASE"

echo "=== Building backend image ==="
docker build --platform linux/amd64 -t cyrt-safe-to-land:latest api/

echo "=== Pushing backend image ==="
docker tag cyrt-safe-to-land:latest "$ECR_BASE/cyrt-safe-to-land:latest"
docker push "$ECR_BASE/cyrt-safe-to-land:latest"

echo "=== Building frontend image ==="
docker build --platform linux/amd64 -t cyrt-frontend:latest frontend/

echo "=== Pushing frontend image ==="
docker tag cyrt-frontend:latest "$ECR_BASE/cyrt-frontend:latest"
docker push "$ECR_BASE/cyrt-frontend:latest"

echo "=== Done ==="
echo "Now run: kubectl apply -f k8s/deployment.yaml"
