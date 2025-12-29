#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="southamerica-east1"
BUCKET_NAME="cabide-catalog-br"
REPO_NAME="cabide-repo"

echo "🚀 Starting Infrastructure Setup in $REGION..."

# 1. Enable Required APIs
echo "Enabling APIs..."
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    drive.googleapis.com

# 2. Create Artifact Registry for Docker Images
echo "Creating Artifact Registry..."
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Cabide AI"

# 3. Create Cloud Storage Bucket in São Paulo
echo "Creating GCS Bucket in Brazil..."
gcloud storage buckets create gs://$BUCKET_NAME \
    --location=$REGION \
    --uniform-bucket-level-access

# 4. Set Bucket Permissions (Optional: Public-read if needed for the app)
# gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
#     --member="allUsers" --role="roles/storage.objectViewer"

echo "✅ Infrastructure Ready!"
echo "Bucket: gs://$BUCKET_NAME"
echo "Registry: $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
