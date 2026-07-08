#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform"

AWS_REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PROJECT_NAME="${PROJECT_NAME:-football-manager}"

cd "$TERRAFORM_DIR"

if ! command -v terraform &>/dev/null; then
  echo "Error: terraform is not installed"
  exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-backend"
ECR_FRONTEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-frontend"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building backend image..."
docker build -f "$ROOT_DIR/backend/Dockerfile.prod" -t "${ECR_BACKEND}:${IMAGE_TAG}" "$ROOT_DIR/backend"

echo "Building frontend image..."
docker build -f "$ROOT_DIR/frontend/Dockerfile.prod" -t "${ECR_FRONTEND}:${IMAGE_TAG}" "$ROOT_DIR/frontend"

echo "Pushing backend image..."
docker push "${ECR_BACKEND}:${IMAGE_TAG}"

echo "Pushing frontend image..."
docker push "${ECR_FRONTEND}:${IMAGE_TAG}"

CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "${PROJECT_NAME}-cluster")
BACKEND_SERVICE=$(terraform output -raw ecs_backend_service 2>/dev/null || echo "${PROJECT_NAME}-backend")
FRONTEND_SERVICE=$(terraform output -raw ecs_frontend_service 2>/dev/null || echo "${PROJECT_NAME}-frontend")

echo "Forcing new ECS deployment..."
aws ecs update-service --cluster "$CLUSTER_NAME" --service "$BACKEND_SERVICE" --force-new-deployment --region "$AWS_REGION" --no-cli-pager
aws ecs update-service --cluster "$CLUSTER_NAME" --service "$FRONTEND_SERVICE" --force-new-deployment --region "$AWS_REGION" --no-cli-pager

echo "Done! Images pushed and ECS services updated."
echo "  Backend:  ${ECR_BACKEND}:${IMAGE_TAG}"
echo "  Frontend: ${ECR_FRONTEND}:${IMAGE_TAG}"
