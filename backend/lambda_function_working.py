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
        
        youtube_url = body.get('url', '').strip()
        email = body.get('email', '').strip()
        
        if not youtube_url or not email:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'URL and email are required'
                })
            }
        
        # Extract video ID from YouTube URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Invalid YouTube URL'
                })
            }
        
        print(f"Processing video: {video_id}")
        
        # For now, let's create a mock response that works
        # This will help us test the rest of the pipeline
        mock_summary = f"""
        This is a mock summary for YouTube video {video_id}.
        
        **Video Title:** Sample Video Title
        **Duration:** 10:30
        **Channel:** Sample Channel
        
        **Key Points:**
        1. Introduction to the topic
        2. Main discussion points
        3. Key takeaways
        4. Conclusion
        
        **Summary:**
        This video discusses important concepts related to the topic. The presenter covers various aspects and provides valuable insights for viewers.
        
        **Note:** This is a demo response. The actual implementation would download the video, transcribe it, and generate a summary using AWS Bedrock.
        """
        
        mock_transcript = f"""
        [00:00] Welcome to this video about the topic.
        [00:30] Today we'll be discussing important concepts.
        [01:00] Let's start with the first point.
        [02:00] Moving on to the second topic.
        [03:00] Here are some key takeaways.
        [04:00] In conclusion, we've covered the main points.
        [04:30] Thank you for watching!
        """
        
        # Save mock data to S3
        summary_key = f"summaries/{video_id}_{uuid.uuid4().hex[:8]}.txt"
        transcript_key = f"transcripts/{video_id}_{uuid.uuid4().hex[:8]}.txt"
        
        # Upload summary to S3
        s3_client.put_object(
            Bucket=SUMMARIES_BUCKET,
            Key=summary_key,
            Body=mock_summary.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # Upload transcript to S3
        s3_client.put_object(
            Bucket=TRANSCRIPTS_BUCKET,
            Key=transcript_key,
            Body=mock_transcript.encode('utf-8'),
            ContentType='text/plain'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'video_id': video_id,
                'summary': mock_summary,
                'transcript': mock_transcript,
                'message': 'Mock summary generated successfully! This is a demo response.',
                'summary_url': f"s3://{SUMMARIES_BUCKET}/{summary_key}",
                'transcript_url': f"s3://{TRANSCRIPTS_BUCKET}/{transcript_key}"
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }

def extract_video_id(url):
    """
    Extract video ID from YouTube URL
    """
    try:
        parsed_url = urlparse(url)
        
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            return parsed_url.path[1:]
        else:
            return None
    except Exception as e:
        print(f"Error extracting video ID: {str(e)}")
        return None

def download_video_audio(url, video_id):
    """
    Download video audio using yt-dlp
    """
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        audio_file = os.path.join(temp_dir, f"{video_id}.mp3")
        
        # Try different yt-dlp paths
        possible_paths = [
            '/opt/python/bin/yt-dlp',
            '/usr/local/bin/yt-dlp',
            'yt-dlp',
            '/opt/python/bin/python -m yt_dlp'
        ]
        
        for yt_dlp_path in possible_paths:
            try:
                if yt_dlp_path.startswith('/opt/python/bin/python'):
                    cmd = yt_dlp_path.split() + [
                        '--extract-audio',
                        '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '--output', audio_file,
                        url
                    ]
                else:
                    cmd = [
                        yt_dlp_path,
                        '--extract-audio',
                        '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '--output', audio_file,
                        url
                    ]
                
                print(f"Trying command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"Successfully downloaded audio to {audio_file}")
                    return audio_file
                else:
                    print(f"yt-dlp error with {yt_dlp_path}: {result.stderr}")
                    continue
                    
            except Exception as e:
                print(f"Error with {yt_dlp_path}: {str(e)}")
                continue
        
        raise Exception("All yt-dlp paths failed")
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        raise Exception(f"Failed to download video audio: {str(e)}")

def upload_to_s3(file_path, bucket, key):
    """
    Upload file to S3
    """
    try:
        s3_client.upload_file(file_path, bucket, key)
        print(f"Uploaded {file_path} to s3://{bucket}/{key}")
        return True
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return False

def start_transcription_job(audio_key, video_id):
    """
    Start AWS Transcribe job
    """
    try:
        job_name = f"transcribe-{video_id}-{int(time.time())}"
        
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f"s3://{RAW_BUCKET}/{audio_key}"},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=TRANSCRIPTS_BUCKET,
            OutputKey=f"transcripts/{video_id}.json"
        )
        
        print(f"Started transcription job: {job_name}")
        return job_name
        
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise Exception(f"Failed to start transcription: {str(e)}")

def wait_for_transcription(job_name, max_wait_time=600):
    """
    Wait for transcription to complete
    """
    try:
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                return response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            elif status == 'FAILED':
                raise Exception("Transcription job failed")
            
            print(f"Transcription status: {status}")
            time.sleep(10)
        
        raise Exception("Transcription timeout")
        
    except Exception as e:
        print(f"Transcription wait error: {str(e)}")
        raise Exception(f"Failed to wait for transcription: {str(e)}")

def get_transcript_from_s3(transcript_uri):
    """
    Get transcript from S3
    """
    try:
        # Parse S3 URI
        s3_uri_parts = transcript_uri.replace('s3://', '').split('/', 1)
        bucket = s3_uri_parts[0]
        key = s3_uri_parts[1]
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        transcript_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Extract text from transcript
        transcript_text = ""
        for item in transcript_data['results']['transcripts']:
            transcript_text += item['transcript'] + " "
        
        return transcript_text.strip()
        
    except Exception as e:
        print(f"Transcript retrieval error: {str(e)}")
        raise Exception(f"Failed to get transcript: {str(e)}")

def generate_summary_with_bedrock(transcript):
    """
    Generate summary using AWS Bedrock
    """
    try:
        prompt = f"""
        Please provide a comprehensive summary of the following video transcript. 
        Include key points, main topics discussed, and important takeaways.
        
        Transcript:
        {transcript}
        
        Please format your response as a clear, well-structured summary.
        """
        
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        })
        
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL,
            body=body,
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        summary = response_body['completion']
        
        return summary
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        # Return a fallback summary if Bedrock fails
        return f"Summary generation failed: {str(e)}. This is a fallback response."

def cleanup_temp_files(temp_dir):
    """
    Clean up temporary files
    """
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
