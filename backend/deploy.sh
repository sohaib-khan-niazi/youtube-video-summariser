#!/bin/bash

# Script to package Lambda function for deployment

echo "🚀 Packaging Lambda function for deployment..."

# Create deployment directory
mkdir -p deployment
cd deployment

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r ../requirements.txt -t .

# Copy Lambda function code
echo "📋 Copying Lambda function code..."
cp ../lambda_function.py .

# Create deployment package
echo "🗜️ Creating deployment package..."
zip -r ../lambda_function.zip .

# Clean up
cd ..
rm -rf deployment

echo "✅ Lambda deployment package created: lambda_function.zip"
echo "📏 Package size: $(du -h lambda_function.zip | cut -f1)"

# Note: You'll need to install yt-dlp binary separately
echo "⚠️  Note: You may need to install yt-dlp binary in your Lambda layer or container"
echo "   For now, the function will work with basic functionality"
