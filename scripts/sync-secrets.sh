#!/bin/bash

# ========================================
# GitHub Secrets Sync Script
# ========================================
# Automatically sync secrets from .env to GitHub repository secrets
# Usage: bash scripts/sync-secrets.sh
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔐 GitHub Secrets Sync Tool"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "   Please create a .env file in the project root."
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: GitHub CLI (gh) is not installed!${NC}"
    echo "   Install it with: brew install gh (macOS) or apt install gh (Ubuntu)"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with GitHub CLI${NC}"
    echo "   Run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Define which env vars should be synced as secrets
# Add or remove variables as needed
SECRETS_TO_SYNC=(
    "GEMINI_API_KEY"
    "GDRIVE_FOLDER_ID"
    "GCP_PROJECT_ID"
)

# Special handling for JSON files
JSON_SECRETS=(
    "GCP_SERVICE_ACCOUNT:gcp-service-account.json"
)

echo "📝 Syncing secrets from .env to GitHub..."
echo ""

# Function to get value from .env
get_env_value() {
    local key=$1
    # Read .env, ignore comments and empty lines, extract value
    grep "^${key}=" .env | cut -d '=' -f2- | sed 's/^["'\'']\(.*\)["'\'']$/\1/'
}

# Sync regular secrets
for secret in "${SECRETS_TO_SYNC[@]}"; do
    value=$(get_env_value "$secret")

    if [ -z "$value" ]; then
        echo -e "${YELLOW}⏭️  Skipping $secret (not found in .env)${NC}"
        continue
    fi

    echo -n "   Syncing $secret... "
    if echo "$value" | gh secret set "$secret" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
done

# Sync JSON file secrets
for entry in "${JSON_SECRETS[@]}"; do
    secret_name="${entry%%:*}"
    file_path="${entry##*:}"

    if [ ! -f "$file_path" ]; then
        echo -e "${YELLOW}⏭️  Skipping $secret_name ($file_path not found)${NC}"
        continue
    fi

    echo -n "   Syncing $secret_name from $file_path... "
    if gh secret set "$secret_name" < "$file_path" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Sync complete!${NC}"
echo ""
echo "📋 Current GitHub secrets:"
gh secret list

echo ""
echo -e "${YELLOW}💡 Tip:${NC} Add this script to your workflow:"
echo "   1. Update .env with new values"
echo "   2. Run: bash scripts/sync-secrets.sh"
echo "   3. Secrets are automatically updated in GitHub"
