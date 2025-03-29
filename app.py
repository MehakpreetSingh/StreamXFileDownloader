import os
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
CORS(app)  # Enable CORS for all routes

@app.route('/api/download', methods=['GET'])
def get_download_link():
    """
    GET endpoint that accepts a file ID and returns download information
    from scloud.ninja website.
    """
    try:
        # Get the file ID from the query parameters, no default needed as it's required
        file_id = request.args.get('id')
        
        if not file_id:
            logger.error("No file ID provided")
            return jsonify({"error": "File ID is required"}), 400
        
        logger.debug(f"GET /api/download with id={file_id}")
        
        # Form the URL with the base URL and the file ID
        base_url = 'https://new4.scloud.ninja/file/'
        file_url = base_url + file_id
        
        # Fetch download link information
        result = fetch_html_link(file_url)
        
        # Return JSON response with appropriate headers
        return jsonify(result), 200, {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': '*'
        }
        
    except Exception as e:
        logger.exception("Failed to fetch data")
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500

def fetch_html_link(link):
    """
    Fetches and parses the HTML from the provided link to extract download information.
    
    Args:
        link (str): The URL of the file page to scrape
        
    Returns:
        dict: Dictionary containing downloadLink, filename, and size
    """
    logger.debug(f"Fetching HTML from: {link}")
    
    # Make request to the file page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    response = requests.get(link, headers=headers)
    response.raise_for_status()  # Raise exception for bad responses
    html = response.text
    
    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract download link
    download_link_element = soup.select_one('a.block')
    download_link = download_link_element.get('href') if download_link_element else ''
    
    # Extract filename and size
    filename_element = soup.select_one('div.space-y-4.mb-6 > div:nth-child(1) > p')
    size_element = soup.select_one('div.space-y-4.mb-6 > div:nth-child(2) > p')
    
    filename = filename_element.text if filename_element else 'Unknown'
    size = size_element.text if size_element else 'Unknown'
    
    logger.debug(f"Extracted download link: {download_link}")
    logger.debug(f"Extracted filename: {filename}")
    logger.debug(f"Extracted size: {size}")
    
    # Return the results
    result = {
        "downloadLink": download_link,
        "filename": filename,
        "size": size
    }
    
    return result

@app.route('/api/search', methods=['GET'])
def search_files():
    """
    GET endpoint that accepts a search query and returns search results
    from scloud.ninja website.
    """
    try:
        # Get the search query from the request parameters, default to 'mufasa' if not provided
        search_query = request.args.get('search', 'mufasa')
        decoded_query = urllib.parse.unquote(search_query)
        
        logger.debug(f"GET /api/search with search=\"{decoded_query}\"")
        
        # Fetch search results
        html = fetch_search_results(decoded_query)
        if not html:
            return jsonify({"error": "Failed to fetch search results"}), 500
            
        # Parse and extract results
        results = parse_search_results(html)
        
        # Return JSON response with appropriate headers
        return jsonify(results), 200, {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': '*'
        }
        
    except Exception as e:
        logger.exception("Failed to fetch search results")
        return jsonify({"error": f"Failed to fetch search results: {str(e)}"}), 500

def fetch_search_results(search_query):
    """
    Fetches search results from scloud.ninja.
    
    Args:
        search_query (str): The search query
        
    Returns:
        str: HTML content of the search results page
    """
    logger.debug(f"Fetching search results for: {search_query}")
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Step 1: Get Search Token
        token_url = 'https://new4.scloud.ninja/get-search-token'
        token_data = f'search_query={urllib.parse.quote(search_query)}'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://new4.scloud.ninja',
            'Referer': 'https://new4.scloud.ninja/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15'
        }
        
        # Send POST request and capture the redirect without following it
        token_response = session.post(
            token_url,
            data=token_data,
            headers=headers,
            allow_redirects=False
        )
        
        # Check if we got a redirect response
        if token_response.status_code != 302:
            logger.error(f"Expected 302 redirect, got {token_response.status_code}")
            return None
            
        # Extract token from the Location header
        location_header = token_response.headers.get('location')
        if not location_header:
            logger.error("No Location header in response")
            return None
            
        # Extract token from redirect URL
        token_match = location_header.split('token=')
        if len(token_match) < 2:
            logger.error(f"Failed to extract token from: {location_header}")
            return None
            
        token = token_match[1]
        logger.debug(f"Extracted Token: {token}")
        
        # Step 2: Fetch search results using the token
        results_url = f'https://new4.scloud.ninja/?token={token}'
        results_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
            'Referer': 'https://new4.scloud.ninja/'
        }
        
        final_response = session.get(results_url, headers=results_headers)
        final_response.raise_for_status()
        
        return final_response.text
        
    except Exception as e:
        logger.exception(f"Error fetching search results: {str(e)}")
        return None

def parse_search_results(html):
    """
    Parses HTML from search results page to extract file information.
    
    Args:
        html (str): HTML content of the search results page
        
    Returns:
        list: List of dictionaries containing file information
    """
    logger.debug("Parsing search results HTML")
    
    try:
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Locate and extract file information from all matching links
        for element in soup.select('a[href]'):
            title_container = element.select_one('.title-container span')
            size_element = element.select_one('span.inline-block')
            link = element.get('href')
            
            if title_container and size_element and link:
                title = title_container.text.strip()
                size = size_element.text.strip()
                
                # Extract just the file ID part of the link
                if link and isinstance(link, str):
                    link_parts = link.split('/')
                    link_id = link_parts[-1] if link_parts else ''
                else:
                    link_id = ''
                
                if title and size and link_id:
                    results.append({
                        "name": title,
                        "size": size,
                        "link": link_id
                    })
        
        logger.debug(f"Found {len(results)} search results")
        return results
        
    except Exception as e:
        logger.exception(f"Error parsing search results: {str(e)}")
        return []

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

# Root route - serve the main interface
@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')
    
# API info page
@app.route('/info', methods=['GET'])
def api_info():
    return app.send_static_file('info.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
