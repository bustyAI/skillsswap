#!/bin/bash
# deploy.sh
# Run this script on your EC2 instance to deploy or redeploy SkillSwap.
# Usage: bash deploy.sh
#
# Prerequisites:
#   - Git repo cloned to ~/skillswap
#   - .env.prod file exists at ~/skillswap/.env.prod
#   - Docker and docker compose installed

set -e  # Exit immediately if any command fails

REPO_DIR="${HOME}/skillswap"
ENV_FILE="${REPO_DIR}/.env.prod"

echo "==> Changing to repo directory..."
cd "$REPO_DIR"

echo "==> Checking for .env.prod..."
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env.prod not found at $ENV_FILE"
    echo ""
    echo "Create it by copying the example:"
    echo "  cp .env.prod.example .env.prod"
    echo "  nano .env.prod  # fill in real values"
    exit 1
fi

echo "==> Pulling latest code from git..."
git pull

echo "==> Pulling latest base images..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" pull

echo "==> Building and starting containers..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d --build

echo "==> Waiting for services to be healthy..."
sleep 5

echo "==> Container status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "==> Deployment complete!"
echo ""
echo "    Test the health endpoint:"
echo "      curl http://localhost:8000/health"
echo ""
echo "    Or from outside the server:"
echo "      curl https://skillsswap.xyz/api/health"
echo ""
echo "    View logs:"
echo "      docker compose -f docker-compose.prod.yml logs -f backend"
