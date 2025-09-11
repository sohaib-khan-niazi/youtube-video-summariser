import json
import boto3
import os
import subprocess
import tempfile
import uuid
from urllib.parse import urlparse, parse_qs
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
bedrock_client = boto3.client('bedrock-runtime')

# Environment variables
RAW_BUCKET = os.environ['RAW_BUCKET']
TRANSCRIPTS_BUCKET = os.environ['TRANSCRIPTS_BUCKET']
SUMMARIES_BUCKET = os.environ['SUMMARIES_BUCKET']
BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0')

def lambda_handler(event, context):
    """
    Main Lambda handler for YouTube video summarization
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        youtube_url = body.get('url')
        email = body.get('email')
        
        if not youtube_url or not email:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'URL and email are required'})
            }
        
        # Extract video ID from YouTube URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid YouTube URL'})
            }
        
        # For now, return a mock response since yt-dlp won't work in Lambda
        # In production, you'd need to use a different approach
        mock_summary = f"This is a mock summary for video {video_id}. The actual implementation would download the video, transcribe it, and generate a summary using Bedrock."
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'summary': mock_summary,
                'transcript': f"Mock transcript for video {video_id}...",
                'video_id': video_id,
                'note': 'This is a demo response. Full implementation requires yt-dlp binary in Lambda layer.'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    try:
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com']:
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.hostname == 'youtu.be':
            return parsed.path[1:]
    except:
        pass
    return None

def generate_summary_bedrock(transcript):
    """Generate summary using AWS Bedrock"""
    prompt = f"""Please summarize this video transcript in 2-3 paragraphs, focusing on the main points and key insights:

{transcript[:4000]}

Summary:"""

    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 500,
        "temperature": 0.7,
        "top_p": 1,
        "stop_sequences": ["\n\nHuman:"]
    })
    
    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL,
        body=body,
        contentType='application/json'
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['completion']
