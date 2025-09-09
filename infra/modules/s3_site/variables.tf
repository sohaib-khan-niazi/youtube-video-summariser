variable "bucket_name" {
  description = "Name of the S3 bucket for website hosting"
  type        = string
}

variable "tags" {
  description = "Common tags to apply"
  type        = map(string)
  default     = {}
}

variable "index_html_content" {
  description = "Content for the index.html file"
  type        = string
  default     = <<-EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Summarizer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
        input, button { padding: 10px; margin: 10px 0; width: 100%; box-sizing: border-box; }
        button { background: #ff0000; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #cc0000; }
        .result { margin-top: 20px; padding: 20px; background: white; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Video Summarizer</h1>
        <p>Enter a YouTube URL and your email to get a summary of the video.</p>
        
        <input type="url" id="youtubeUrl" placeholder="https://www.youtube.com/watch?v=..." required>
        <input type="email" id="email" placeholder="your.email@example.com" required>
        <button onclick="summarizeVideo()">Summarize Video</button>
        
        <div id="result" class="result" style="display: none;">
            <h3>Summary:</h3>
            <p id="summaryText"></p>
        </div>
    </div>

    <script>
        async function summarizeVideo() {
            const url = document.getElementById('youtubeUrl').value;
            const email = document.getElementById('email').value;
            const resultDiv = document.getElementById('result');
            const summaryText = document.getElementById('summaryText');
            
            if (!url || !email) {
                alert('Please enter both YouTube URL and email');
                return;
            }
            
            summaryText.textContent = 'Processing... Please wait.';
            resultDiv.style.display = 'block';
            
            try {
                const response = await fetch('API_GATEWAY_URL/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url, email: email })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    summaryText.textContent = data.summary || 'Summary generated successfully!';
                } else {
                    summaryText.textContent = 'Error: ' + (data.error || 'Failed to process video');
                }
            } catch (error) {
                summaryText.textContent = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
EOF
}

variable "error_html_content" {
  description = "Content for the error.html file"
  type        = string
  default     = <<-EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - YouTube Video Summarizer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
        .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Oops! Something went wrong</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go back to home</a>
    </div>
</body>
</html>
EOF
}
