#!/bin/bash

# Admin Dashboard Deployment Script
# This script builds and deploys the admin dashboard

set -e  # Exit on error

echo "🚀 Admin Dashboard Deployment Script"
echo "===================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with required environment variables"
    echo "See .env.example for reference"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$VITE_GITHUB_TOKEN" ] || [ -z "$VITE_GITHUB_OWNER" ] || [ -z "$VITE_GITHUB_REPO" ]; then
    echo "❌ Error: Missing required environment variables"
    echo "Required: VITE_GITHUB_TOKEN, VITE_GITHUB_OWNER, VITE_GITHUB_REPO"
    exit 1
fi

echo "✅ Environment variables validated"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Run tests
echo "🧪 Running tests..."
npm test

# Build the application
echo "🔨 Building application..."
npm run build

echo "✅ Build completed successfully!"
echo "📁 Build output: dist/"

# Deployment options
echo ""
echo "Deployment Options:"
echo "1. Co-located with Web Server"
echo "2. Netlify"
echo "3. Vercel"
echo "4. AWS S3"
echo "5. Skip deployment (build only)"
echo ""
read -p "Select deployment option (1-5): " option

case $option in
    1)
        echo "📤 Deploying to Web Server..."
        # Copy dist to web server static directory
        if [ -d "../app/static/admin" ]; then
            rm -rf ../app/static/admin
        fi
        mkdir -p ../app/static/admin
        cp -r dist/* ../app/static/admin/
        echo "✅ Deployed to ../app/static/admin/"
        echo "Access at: http://localhost:8000/admin"
        ;;
    2)
        echo "📤 Deploying to Netlify..."
        if ! command -v netlify &> /dev/null; then
            echo "❌ Netlify CLI not found. Installing..."
            npm install -g netlify-cli
        fi
        netlify deploy --prod --dir=dist
        echo "✅ Deployed to Netlify"
        ;;
    3)
        echo "📤 Deploying to Vercel..."
        if ! command -v vercel &> /dev/null; then
            echo "❌ Vercel CLI not found. Installing..."
            npm install -g vercel
        fi
        vercel --prod
        echo "✅ Deployed to Vercel"
        ;;
    4)
        echo "📤 Deploying to AWS S3..."
        read -p "Enter S3 bucket name: " bucket_name
        if [ -z "$bucket_name" ]; then
            echo "❌ Bucket name required"
            exit 1
        fi
        aws s3 sync dist/ s3://$bucket_name --delete
        echo "✅ Deployed to S3: s3://$bucket_name"
        ;;
    5)
        echo "⏭️  Skipping deployment"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment complete!"
