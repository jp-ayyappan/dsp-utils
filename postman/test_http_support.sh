#!/bin/bash

# Test HTTP support for DSP gRPC services
# Usage: ./test_http_support.sh <base_url> <bearer_token>

BASE_URL="${1:-https://platform.acme.com:443}"
TOKEN="${2}"

if [ -z "$TOKEN" ]; then
  echo "Usage: $0 <base_url> <bearer_token>"
  echo "Example: $0 https://platform.acme.com:443 eyJhbGc..."
  exit 1
fi

echo "Testing HTTP support for gRPC services..."
echo "Base URL: $BASE_URL"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
  local service=$1
  local method=$2
  local requires_auth=$3
  local url="${BASE_URL}/${service}/${method}"

  echo -n "Testing ${service}/${method}... "

  if [ "$requires_auth" = "true" ]; then
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{}' 2>&1)
  else
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
      -H "Content-Type: application/json" \
      -d '{}' 2>&1)
  fi

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)

  # Check if it's a valid HTTP response
  if [[ $http_code =~ ^[0-9]+$ ]] && [ $http_code -ge 200 ] && [ $http_code -lt 500 ]; then
    echo -e "${GREEN}✓ HTTP SUPPORTED${NC} (HTTP $http_code)"
    return 0
  else
    echo -e "${RED}✗ gRPC-only${NC} (HTTP $http_code)"
    return 1
  fi
}

echo "=== Testing Services Without Explicit HTTP Annotations ==="
echo ""

# Policy Actions
test_endpoint "policy.actions.ActionService" "ListActions" true

# Policy Registered Resources
test_endpoint "policy.registeredresources.RegisteredResourcesService" "ListRegisteredResources" true

# Policy Key Management
test_endpoint "policy.keymanagement.KeyManagementService" "ListProviderConfigs" true

# Policy Obligations
test_endpoint "policy.obligations.Service" "ListObligations" true

# Authorization v2
test_endpoint "authorization.v2.AuthorizationService" "GetEntitlements" true

# Version Service (no auth)
test_endpoint "version.v1.VersionService" "GetVersion" false

# Config Service
test_endpoint "config.v1.ConfigService" "GetTaggingPDPConfig" true

# Web Admin
test_endpoint "webadmin.v1.ConfigService" "ListAllConfig" true

# Entity Resolution v2
test_endpoint "entityresolution.v2.EntityResolutionService" "ResolveEntities" true

# Shared v2
test_endpoint "shared.v2.SharedService" "GetMyEntitlements" true

# Certificate Service
test_endpoint "virtru.policy.certificates.v1.CertificateService" "ListCertificatesByNamespace" true

# Health Check (no auth)
test_endpoint "grpc.health.v1.Health" "Check" false

echo ""
echo "=== Testing Complete ==="
echo ""
echo -e "${YELLOW}Note: Services marked with ✓ can be added to Postman collection${NC}"
echo -e "${YELLOW}Services marked with ✗ require pure gRPC (use grpcurl)${NC}"
