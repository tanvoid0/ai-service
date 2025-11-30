#!/bin/bash
# GCP Cloud Run Deployment Script

set -e

echo "🚀 Deploying AI Service to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📦 Project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com --quiet

# Deploy to Cloud Run
echo "🏗️  Building and deploying..."
gcloud run deploy ai-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "ENABLE_SECURITY_SERVICE=false,DEFAULT_PROVIDER=gemini,FLASK_ENV=production" \
  --quiet

echo "✅ Deployment complete!"
echo "📝 Don't forget to set environment variables:"
echo "   - HARDCODED_API_KEY"
echo "   - GEMINI_API_KEY"
echo ""
echo "Run: gcloud run services update ai-service --update-env-vars HARDCODED_API_KEY=your-key,GEMINI_API_KEY=your-key"

