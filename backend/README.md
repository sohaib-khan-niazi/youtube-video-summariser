# YouTube Video Summarizer - Backend

This directory contains the Lambda function code for the YouTube Video Summarizer.

## Architecture

The Lambda function handles the complete video processing pipeline:

1. **Download**: Uses `yt-dlp` to download audio from YouTube
2. **Transcribe**: Uses AWS Transcribe to convert audio to text
3. **Summarize**: Uses OpenAI or AWS Bedrock to generate AI summaries
4. **Store**: Saves results to S3 buckets
5. **Cleanup**: Removes temporary files

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Package for Deployment

```bash
./deploy.sh
```

This creates `lambda_function.zip` which is used by Terraform.

### 3. Configure AI Service

You can use either OpenAI or AWS Bedrock for summarization:

#### Option A: OpenAI
1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Set it in your `terraform.tfvars`:
   ```hcl
   openai_api_key = "your-api-key-here"
   ```

#### Option B: AWS Bedrock (Default)
- Uses Claude 3 Sonnet model
- No additional setup required
- Make sure Bedrock is enabled in your AWS region

## Environment Variables

The Lambda function expects these environment variables:

- `RAW_BUCKET`: S3 bucket for temporary audio files
- `TRANSCRIPTS_BUCKET`: S3 bucket for transcription results
- `SUMMARIES_BUCKET`: S3 bucket for final summaries
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `BEDROCK_MODEL`: Bedrock model ID (default: Claude 3 Sonnet)

## API Endpoint

The function is exposed via API Gateway at:
```
POST /summarize
```

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "email": "user@example.com"
}
```

Response:
```json
{
  "summary": "AI-generated summary...",
  "transcript": "First 500 characters of transcript...",
  "video_id": "extracted-video-id"
}
```

## Limitations

- Maximum Lambda execution time: 15 minutes
- Maximum memory: 1GB
- Video length: Recommended under 2 hours
- Audio format: MP3 (automatically converted)

## Troubleshooting

### Common Issues

1. **yt-dlp not found**: The binary needs to be included in the deployment package
2. **Transcription timeout**: Very long videos may exceed Lambda timeout
3. **Memory issues**: Large videos may require more memory allocation

### Logs

Check CloudWatch logs at:
```
/aws/lambda/{function-name}
```

## Development

To test locally:

```python
import json
from lambda_function import lambda_handler

event = {
    'body': json.dumps({
        'url': 'https://www.youtube.com/watch?v=...',
        'email': 'test@example.com'
    })
}

result = lambda_handler(event, {})
print(result)
```
