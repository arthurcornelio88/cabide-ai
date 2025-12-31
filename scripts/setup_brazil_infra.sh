#!/bin/bash

# ========================================
# Cabide AI Infrastructure Setup Script
# ========================================
# This script sets up the complete GCP infrastructure for Cabide AI:
# - Artifact Registry for Docker images
# - Cloud Run service for the backend API
# - Required APIs and permissions
# ========================================

set -e  # Exit on error

# Configuration
PROJECT_ID="gen-lang-client-0410722440"
REGION="southamerica-east1"
REPO_NAME="cabide-repo"
SERVICE_NAME="cabide-api"

echo "🚀 Starting Infrastructure Setup for Cabide AI..."
echo "📍 Project: $PROJECT_ID"
echo "📍 Region: $REGION (São Paulo, Brazil)"
echo ""

# 1. Set active project
echo "1️⃣ Setting active GCP project..."
gcloud config set project $PROJECT_ID

# 2. Enable Required APIs
echo ""
echo "2️⃣ Enabling required Google Cloud APIs..."
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    drive.googleapis.com \
    aiplatform.googleapis.com

echo "✅ APIs enabled successfully"

# 3. Create Artifact Registry for Docker Images
echo ""
echo "3️⃣ Creating Artifact Registry repository..."
if gcloud artifacts repositories describe $REPO_NAME --location=$REGION &>/dev/null; then
    echo "ℹ️  Repository '$REPO_NAME' already exists, skipping creation"
else
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Cabide AI Backend"
    echo "✅ Artifact Registry created"
fi

# 4. Create Cloud Run service (initial placeholder)
echo ""
echo "4️⃣ Creating Cloud Run service..."
if gcloud run services describe $SERVICE_NAME --region=$REGION &>/dev/null; then
    echo "ℹ️  Service '$SERVICE_NAME' already exists, skipping creation"
else
    gcloud run deploy $SERVICE_NAME \
        --image=us-docker.pkg.dev/cloudrun/container/hello \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --quiet
    echo "✅ Cloud Run service created (placeholder image)"
fi

# 5. Summary
echo ""
echo "🎉 Infrastructure setup complete!"
echo ""
echo "📦 Artifact Registry:"
echo "   $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
echo ""
echo "🚀 Cloud Run Service:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "📝 Next steps:"
echo "   1. Update GitHub Secrets with PROJECT_ID: $PROJECT_ID"
echo "   2. Push to 'main' branch to trigger automatic deployment"
echo "   3. Configure Streamlit Cloud with backend URL"
echo ""
