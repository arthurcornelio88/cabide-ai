#!/bin/bash

# ========================================
# Cabide AI Infrastructure Setup Script
# ========================================
# This script sets up the complete GCP infrastructure for Cabide AI:
# - Service accounts with proper permissions
# - Artifact Registry for Docker images
# - Cloud Run service for the backend API (with IAM authentication)
# - Required APIs and permissions
# ========================================

set -e  # Exit on error

# Configuration
PROJECT_ID="gen-lang-client-0410722440"
REGION="southamerica-east1"
REPO_NAME="cabide-repo"
SERVICE_NAME="cabide-api"
DEPLOYER_SA="cabide-ai-uploader"
INVOKER_SA="cabide-streamlit-invoker"

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
    aiplatform.googleapis.com \
    iam.googleapis.com

echo "✅ APIs enabled successfully"

# 3. Create Service Accounts
echo ""
echo "3️⃣ Creating service accounts..."

# Deployer SA (for GitHub Actions)
if gcloud iam service-accounts describe ${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
    echo "ℹ️  Service account '$DEPLOYER_SA' already exists"
else
    gcloud iam service-accounts create $DEPLOYER_SA \
        --display-name="Cabide AI Deployer" \
        --description="Service account for GitHub Actions deployments"
    echo "✅ Deployer service account created"
fi

# Invoker SA (for Streamlit Cloud to call backend)
if gcloud iam service-accounts describe ${INVOKER_SA}@${PROJECT_ID}.iam.gserviceaccount.com &>/dev/null; then
    echo "ℹ️  Service account '$INVOKER_SA' already exists"
else
    gcloud iam service-accounts create $INVOKER_SA \
        --display-name="Cabide Streamlit Invoker" \
        --description="Service account for Streamlit Cloud to invoke Cloud Run backend"
    echo "✅ Invoker service account created"
fi

# 4. Grant IAM Permissions
echo ""
echo "4️⃣ Configuring IAM permissions..."

# Deployer SA permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin" \
    --condition=None \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" \
    --condition=None \
    --quiet

echo "✅ IAM permissions configured"

echo ""
echo "ℹ️  Note: Google Drive access for ${INVOKER_SA} must be configured manually:"
echo "   1. Share the Google Drive folder with: ${INVOKER_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   2. Grant 'Editor' permission to the service account"

# 5. Create Artifact Registry for Docker Images
echo ""
echo "5️⃣ Creating Artifact Registry repository..."
if gcloud artifacts repositories describe $REPO_NAME --location=$REGION &>/dev/null; then
    echo "ℹ️  Repository '$REPO_NAME' already exists, skipping creation"
else
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Cabide AI Backend"
    echo "✅ Artifact Registry created"
fi

# 6. Create Cloud Run service (initial placeholder with public access for OAuth)
echo ""
echo "6️⃣ Creating Cloud Run service..."
if gcloud run services describe $SERVICE_NAME --region=$REGION &>/dev/null; then
    echo "ℹ️  Service '$SERVICE_NAME' already exists, updating IAM policy..."
else
    gcloud run deploy $SERVICE_NAME \
        --image=us-docker.pkg.dev/cloudrun/container/hello \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --service-account=${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com \
        --quiet
    echo "✅ Cloud Run service created (placeholder image, public access enabled)"
    echo "ℹ️  Public access is required for OAuth callback endpoint"
fi

# 7. Grant Cloud Run Invoker permission to Streamlit SA and authorized users
echo ""
echo "7️⃣ Granting Cloud Run invoke permissions..."

# Allow Streamlit service account to invoke
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="serviceAccount:${INVOKER_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --quiet

# Allow authorized users (for testing via browser)
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="user:arthur.cornelio@gmail.com" \
    --role="roles/run.invoker" \
    --quiet

gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="user:elzamoraes.contato@gmail.com" \
    --role="roles/run.invoker" \
    --quiet

echo "✅ Cloud Run invoke permissions granted"

# 8. Grant public access for OAuth callback endpoint
echo ""
echo "8️⃣ Enabling public access for OAuth callback..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --quiet

echo "✅ Public access enabled for OAuth callback endpoint"
echo "ℹ️  Note: This is required for Google OAuth redirect to work"
echo "ℹ️  The /oauth/callback endpoint needs to be publicly accessible"

# 9. Summary
echo ""
echo "🎉 Infrastructure setup complete!"
echo ""
echo "📦 Artifact Registry:"
echo "   $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
echo ""
echo "🚀 Cloud Run Service:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "🔐 Service Accounts Created:"
echo "   Deployer: ${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   Invoker:  ${INVOKER_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "👥 Authorized Users:"
echo "   - arthur.cornelio@gmail.com"
echo "   - elzamoraes.contato@gmail.com"
echo ""
echo "🔓 Security Note:"
echo "   - Service has PUBLIC access enabled for OAuth callback endpoint (/oauth/callback)"
echo "   - This is REQUIRED for Google OAuth to redirect users back to the app"
echo "   - Other endpoints can implement their own authentication as needed"
echo ""
echo "📝 Next steps:"
echo "   1. Download key for deployer SA: gcloud iam service-accounts keys create deployer-sa-key.json --iam-account=${DEPLOYER_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   2. Update GitHub Secrets with deployer SA key (GCP_SERVICE_ACCOUNT)"
echo "   3. Configure OAuth in Google Cloud Console (see OAUTH_SETUP.md)"
echo "   4. Push to 'main' branch to trigger automatic deployment"
echo ""
