import json
import boto3
import os
import subprocess
import tempfile
import uuid
import time
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
        
        print(f"Processing video: {video_id}")
        
        # Step 1: Download video audio
        audio_file_path = download_video_audio(youtube_url, video_id)
        if not audio_file_path:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Failed to download video audio'})
            }
        
        # Step 2: Upload audio to S3
        audio_s3_key = f"audio/{video_id}_{uuid.uuid4().hex}.mp3"
        upload_audio_to_s3(audio_file_path, audio_s3_key)
        
        # Step 3: Start transcription job
        job_name = f"transcribe-{video_id}-{int(time.time())}"
        start_transcription_job(job_name, audio_s3_key)
        
        # Step 4: Wait for transcription to complete
        transcript_text = wait_for_transcription(job_name)
        if not transcript_text:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Failed to transcribe audio'})
            }
        
        # Step 5: Generate summary using Bedrock
        summary = generate_summary_bedrock(transcript_text)
        
        # Step 6: Save transcript and summary to S3
        transcript_key = f"transcripts/{video_id}_{int(time.time())}.txt"
        summary_key = f"summaries/{video_id}_{int(time.time())}.txt"
        
        save_to_s3(TRANSCRIPTS_BUCKET, transcript_key, transcript_text)
        save_to_s3(SUMMARIES_BUCKET, summary_key, summary)
        
        # Step 7: Clean up temporary files
        cleanup_temp_files(audio_file_path)
        cleanup_s3_audio(audio_s3_key)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'summary': summary,
                'transcript': transcript_text[:1000] + '...' if len(transcript_text) > 1000 else transcript_text,
                'video_id': video_id,
                'transcript_key': transcript_key,
                'summary_key': summary_key
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

def download_video_audio(url, video_id):
    """Download video audio using yt-dlp"""
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        audio_file = os.path.join(temp_dir, f"{video_id}.mp3")
        
        # yt-dlp command to extract audio
        cmd = [
            '/opt/python/bin/yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--output', audio_file,
            url
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return None
        
        # Check if file was created
        if os.path.exists(audio_file):
            print(f"Audio downloaded successfully: {audio_file}")
            return audio_file
        else:
            print("Audio file not created")
            return None
            
    except subprocess.TimeoutExpired:
        print("yt-dlp timeout")
        return None
    except Exception as e:
        print(f"Download error: {str(e)}")
        return None

def upload_audio_to_s3(audio_file_path, s3_key):
    """Upload audio file to S3"""
    try:
        s3_client.upload_file(audio_file_path, RAW_BUCKET, s3_key)
        print(f"Audio uploaded to S3: s3://{RAW_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        raise

def start_transcription_job(job_name, audio_s3_key):
    """Start AWS Transcribe job"""
    try:
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{RAW_BUCKET}/{audio_s3_key}'},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=TRANSCRIPTS_BUCKET,
            OutputKey=f'transcribe-output/{job_name}.json'
        )
        print(f"Transcription job started: {job_name}")
    except Exception as e:
        print(f"Transcription start error: {str(e)}")
        raise

def wait_for_transcription(job_name, max_wait=300):
    """Wait for transcription to complete and return transcript text"""
    try:
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get transcript from S3
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcript_key = transcript_uri.split('/')[-1]
                
                # Download and parse transcript
                transcript_obj = s3_client.get_object(
                    Bucket=TRANSCRIPTS_BUCKET,
                    Key=f'transcribe-output/{transcript_key}'
                )
                
                transcript_data = json.loads(transcript_obj['Body'].read())
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                
                print(f"Transcription completed: {len(transcript_text)} characters")
                return transcript_text
                
            elif status == 'FAILED':
                print(f"Transcription failed: {response['TranscriptionJob'].get('FailureReason', 'Unknown error')}")
                return None
            
            time.sleep(10)  # Wait 10 seconds before checking again
        
        print("Transcription timeout")
        return None
        
    except Exception as e:
        print(f"Transcription wait error: {str(e)}")
        return None

def generate_summary_bedrock(transcript):
    """Generate summary using AWS Bedrock"""
    try:
        prompt = f"""Please provide a comprehensive summary of this video transcript in 2-3 paragraphs, focusing on the main points, key insights, and important takeaways:

{transcript[:4000]}

Summary:"""

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
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
        summary = response_body['completion'].strip()
        
        print(f"Summary generated: {len(summary)} characters")
        return summary
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        # Fallback to simple summary
        return f"This video discusses: {transcript[:500]}..."

def save_to_s3(bucket, key, content):
    """Save content to S3"""
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType='text/plain'
        )
        print(f"Saved to S3: s3://{bucket}/{key}")
    except Exception as e:
        print(f"S3 save error: {str(e)}")
        raise

def cleanup_temp_files(audio_file_path):
    """Clean up temporary files"""
    try:
        if audio_file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            os.rmdir(os.path.dirname(audio_file_path))
            print("Temporary files cleaned up")
    except Exception as e:
        print(f"Cleanup error: {str(e)}")

def cleanup_s3_audio(s3_key):
    """Clean up audio file from S3"""
    try:
        s3_client.delete_object(Bucket=RAW_BUCKET, Key=s3_key)
        print(f"Audio file deleted from S3: {s3_key}")
    except Exception as e:
        print(f"S3 cleanup error: {str(e)}")
