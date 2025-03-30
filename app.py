import os
import logging
from flask import Flask, render_template
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
app.register_blueprint(api_bp)

if __name__ == "__main__":
    # This block will be executed when running the script directly
    # The port is set to 5000 for frontend visibility
    app.run(host="0.0.0.0", port=3000, debug=True)