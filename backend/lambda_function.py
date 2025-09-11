import json
import boto3
import os
import subprocess
import tempfile
import uuid
from urllib.parse import urlparse, parse_qs
import openai
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
bedrock_client = boto3.client('bedrock-runtime')

# Environment variables
RAW_BUCKET = os.environ['RAW_BUCKET']
TRANSCRIPTS_BUCKET = os.environ['TRANSCRIPTS_BUCKET']
SUMMARIES_BUCKET = os.environ['SUMMARIES_BUCKET']
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
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
        
        # Step 1: Download audio using yt-dlp
        audio_key = f"audio/{video_id}.mp3"
        download_audio(youtube_url, audio_key)
        
        # Step 2: Transcribe audio using AWS Transcribe
        transcript = transcribe_audio(audio_key, video_id)
        
        # Step 3: Generate summary using AI
        summary = generate_summary(transcript)
        
        # Step 4: Save summary to S3
        summary_key = f"summaries/{video_id}.json"
        save_summary(summary_key, {
            'video_id': video_id,
            'url': youtube_url,
            'email': email,
            'transcript': transcript,
            'summary': summary,
            'timestamp': context.aws_request_id
        })
        
        # Step 5: Clean up temporary audio file
        cleanup_audio(audio_key)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'summary': summary,
                'transcript': transcript[:500] + '...' if len(transcript) > 500 else transcript,
                'video_id': video_id
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

def download_audio(url, s3_key):
    """Download audio from YouTube and upload to S3"""
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_file = os.path.join(temp_dir, 'audio.mp3')
        
        # Use yt-dlp to download audio
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--output', audio_file.replace('.mp3', '.%(ext)s'),
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to download audio: {result.stderr}")
        
        # Upload to S3
        s3_client.upload_file(audio_file, RAW_BUCKET, s3_key)
        print(f"Uploaded audio to s3://{RAW_BUCKET}/{s3_key}")

def transcribe_audio(s3_key, video_id):
    """Transcribe audio using AWS Transcribe"""
    job_name = f"transcribe-{video_id}-{uuid.uuid4().hex[:8]}"
    
    # Start transcription job
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f's3://{RAW_BUCKET}/{s3_key}'},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=TRANSCRIPTS_BUCKET,
        OutputKey=f"transcripts/{video_id}.json"
    )
    
    # Wait for job completion
    while True:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        
        if status == 'COMPLETED':
            break
        elif status == 'FAILED':
            raise Exception(f"Transcription failed: {response['TranscriptionJob'].get('FailureReason', 'Unknown error')}")
        
        # Wait 10 seconds before checking again
        import time
        time.sleep(10)
    
    # Download and parse transcript
    transcript_key = f"transcripts/{video_id}.json"
    response = s3_client.get_object(Bucket=TRANSCRIPTS_BUCKET, Key=transcript_key)
    transcript_data = json.loads(response['Body'].read())
    
    # Extract text from transcript
    transcript_text = ""
    for item in transcript_data['results']['transcripts']:
        transcript_text += item['transcript'] + " "
    
    return transcript_text.strip()

def generate_summary(transcript):
    """Generate summary using OpenAI or Bedrock"""
    if OPENAI_API_KEY:
        return generate_summary_openai(transcript)
    else:
        return generate_summary_bedrock(transcript)

def generate_summary_openai(transcript):
    """Generate summary using OpenAI"""
    openai.api_key = OPENAI_API_KEY
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that creates concise, informative summaries of video transcripts. Focus on the main points and key insights."
            },
            {
                "role": "user",
                "content": f"Please summarize this video transcript in 2-3 paragraphs:\n\n{transcript[:4000]}"  # Limit to avoid token limits
            }
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content

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

def save_summary(s3_key, summary_data):
    """Save summary to S3"""
    s3_client.put_object(
        Bucket=SUMMARIES_BUCKET,
        Key=s3_key,
        Body=json.dumps(summary_data, indent=2),
        ContentType='application/json'
    )
    print(f"Saved summary to s3://{SUMMARIES_BUCKET}/{s3_key}")

def cleanup_audio(s3_key):
    """Delete temporary audio file from S3"""
    try:
        s3_client.delete_object(Bucket=RAW_BUCKET, Key=s3_key)
        print(f"Cleaned up audio file: s3://{RAW_BUCKET}/{s3_key}")
    except ClientError as e:
        print(f"Warning: Failed to cleanup audio file: {e}")
