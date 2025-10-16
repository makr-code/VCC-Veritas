#!/bin/bash
# ======================================================================
# VERITAS Framework - Kubernetes Deployment Script
# Deploys VERITAS to Kubernetes using Helm
# ======================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-production}"
NAMESPACE="veritas-${ENVIRONMENT}"
RELEASE_NAME="veritas"
CHART_PATH="./helm/veritas"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}VERITAS Kubernetes Deployment${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Namespace: ${YELLOW}${NAMESPACE}${NC}"
echo ""

# Validate environment
if [[ ! "${ENVIRONMENT}" =~ ^(production|staging|dev)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Use: production, staging, or dev${NC}"
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm not found. Please install Helm 3.${NC}"
    exit 1
fi

# Check if chart exists
if [ ! -f "${CHART_PATH}/Chart.yaml" ]; then
    echo -e "${RED}Error: Helm chart not found at ${CHART_PATH}${NC}"
    exit 1
fi

# Select values file
if [ "${ENVIRONMENT}" == "production" ]; then
    VALUES_FILE="${CHART_PATH}/values.yaml"
elif [ "${ENVIRONMENT}" == "staging" ]; then
    VALUES_FILE="${CHART_PATH}/values-staging.yaml"
else
    VALUES_FILE="${CHART_PATH}/values-dev.yaml"
fi

if [ ! -f "${VALUES_FILE}" ]; then
    echo -e "${YELLOW}Warning: Values file ${VALUES_FILE} not found. Using default values.yaml${NC}"
    VALUES_FILE="${CHART_PATH}/values.yaml"
fi

echo -e "${BLUE}Step 1: Creating namespace...${NC}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo -e "${BLUE}Step 2: Checking for existing release...${NC}"
if helm status "${RELEASE_NAME}" -n "${NAMESPACE}" &> /dev/null; then
    echo -e "${YELLOW}Release exists. Performing upgrade...${NC}"
    
    helm upgrade "${RELEASE_NAME}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --values "${VALUES_FILE}" \
        --wait \
        --timeout 10m \
        --atomic \
        --cleanup-on-fail
    
    echo -e "${GREEN}✓ Upgrade completed${NC}"
else
    echo -e "${YELLOW}No existing release found. Performing fresh install...${NC}"
    
    helm install "${RELEASE_NAME}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --values "${VALUES_FILE}" \
        --wait \
        --timeout 10m \
        --atomic \
        --cleanup-on-fail
    
    echo -e "${GREEN}✓ Installation completed${NC}"
fi

echo ""
echo -e "${BLUE}Step 3: Verifying deployment...${NC}"
kubectl get all -n "${NAMESPACE}"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "Release: ${YELLOW}${RELEASE_NAME}${NC}"
echo -e "Namespace: ${YELLOW}${NAMESPACE}${NC}"
echo -e "Chart: ${YELLOW}${CHART_PATH}${NC}"
echo -e "Values: ${YELLOW}${VALUES_FILE}${NC}"

echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View pods:     ${YELLOW}kubectl get pods -n ${NAMESPACE}${NC}"
echo -e "  View logs:     ${YELLOW}kubectl logs -f <pod-name> -n ${NAMESPACE}${NC}"
echo -e "  View services: ${YELLOW}kubectl get svc -n ${NAMESPACE}${NC}"
echo -e "  View ingress:  ${YELLOW}kubectl get ingress -n ${NAMESPACE}${NC}"
echo -e "  Port forward:  ${YELLOW}kubectl port-forward svc/veritas-api 8000:8000 -n ${NAMESPACE}${NC}"

echo ""
echo -e "${GREEN}✓ Deployment successful!${NC}"
