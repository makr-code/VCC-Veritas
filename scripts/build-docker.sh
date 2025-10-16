#!/bin/bash
# ======================================================================
# VERITAS Framework - Docker Build Script
# Builds all production Docker images
# ======================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-}"
VERSION="${VERSION:-latest}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}VERITAS Docker Build${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "Version: ${YELLOW}${VERSION}${NC}"
echo -e "Git Commit: ${YELLOW}${GIT_COMMIT}${NC}"
echo -e "Build Date: ${YELLOW}${BUILD_DATE}${NC}"
echo ""

# Build arguments
BUILD_ARGS="--build-arg BUILD_DATE=${BUILD_DATE} --build-arg GIT_COMMIT=${GIT_COMMIT}"

# Function to build image
build_image() {
    local name=$1
    local dockerfile=$2
    local tag="${REGISTRY}${REGISTRY:+/}veritas/${name}:${VERSION}"
    
    echo -e "${GREEN}Building ${name}...${NC}"
    docker build ${BUILD_ARGS} \
        -t "${tag}" \
        -t "${REGISTRY}${REGISTRY:+/}veritas/${name}:latest" \
        -f "${dockerfile}" \
        .
    
    echo -e "${GREEN}✓ Built ${tag}${NC}"
    echo ""
}

# Build all images
build_image "api" "Dockerfile.production"
build_image "worker" "Dockerfile.worker"
build_image "nginx" "Dockerfile.nginx"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Build Summary${NC}"
echo -e "${GREEN}======================================${NC}"
docker images | grep "veritas"

echo ""
echo -e "${GREEN}✓ All images built successfully!${NC}"
echo ""
echo -e "To push images to registry:"
echo -e "  ${YELLOW}docker push ${REGISTRY}${REGISTRY:+/}veritas/api:${VERSION}${NC}"
echo -e "  ${YELLOW}docker push ${REGISTRY}${REGISTRY:+/}veritas/worker:${VERSION}${NC}"
echo -e "  ${YELLOW}docker push ${REGISTRY}${REGISTRY:+/}veritas/nginx:${VERSION}${NC}"
