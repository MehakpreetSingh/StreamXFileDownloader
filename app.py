import os
import logging
import requests
import urllib.parse
from flask import Flask, render_template, request, Response, stream_with_context
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Enable CORS
CORS(app)

# Routes
@app.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')

@app.route('/info')
def info():
    """Render the API documentation page."""
    return render_template('info.html')

@app.route('/anime')
def anime():
    """Render the anime list page."""
    return render_template('anime.html')

@app.route('/anime/details/<path:anime_id>')
def anime_details(anime_id):
    """Render the anime details page."""
    return render_template('anime_details.html', anime_id=anime_id)

@app.route('/anime/<path:anime_id>/watch/<episode_number>')
def watch_episode(anime_id, episode_number):
    """Render video player page for streaming."""
    source_url = request.args.get('source')
    if not source_url:
        return render_template('error.html', message="No video source provided"), 400
    
    # For now, use a simple anime title from the ID
    anime_title = anime_id.split('/')[-1].replace('_', ' ')
    if '(' in anime_title:
        anime_title = anime_title.split('(')[0].strip()
    
    return render_template('video_player.html', 
                         anime_id=anime_id, 
                         episode_number=episode_number, 
                         anime_title=anime_title,
                         source_url=source_url)

@app.route('/anime/stream')
def stream_video():
    """Proxy stream from remote video source."""
    video_url = request.args.get('url')
    if not video_url:
        return "No video URL provided", 400
    
    # Handle range requests for partial content (essential for proper video streaming)
    range_header = request.headers.get('Range', None)
    headers = {}
    if range_header:
        headers['Range'] = range_header
    
    try:
        # Stream the video content
        req = requests.get(video_url, stream=True, headers=headers)
        if not req.ok:
            return f"Failed to fetch video: Status code {req.status_code}", 500
        
        # Forward the headers
        response_headers = {}
        for header, value in req.headers.items():
            if header.lower() in ('content-type', 'content-length', 'accept-ranges', 'content-range', 'cache-control'):
                response_headers[header] = value
        
        # Add custom cache headers to improve performance
        if 'cache-control' not in response_headers:
            response_headers['Cache-Control'] = 'public, max-age=3600'
        
        # Create a streaming response with larger chunk size for better performance
        def generate():
            for chunk in req.iter_content(chunk_size=65536):  # 64KB chunks for better performance
                yield chunk
                
        return Response(stream_with_context(generate()), 
                      headers=response_headers,
                      status=req.status_code)
    except Exception as e:
        logger.error(f"Error streaming video: {str(e)}")
        return f"Error streaming video: {str(e)}", 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}, 200

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    return {"error": "Internal server error"}, 500

# Import routes after app is created to avoid circular imports
from routes.api import api_bp

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == "__main__":
    # This block will be executed when running the script directly
    # The port is set to 5000 for frontend visibility
    app.run(host="0.0.0.0", port=3000, debug=True)