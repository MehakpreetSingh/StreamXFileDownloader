import os
import logging
import requests
import urllib.parse
import time
import random
import json
import tempfile
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Import trafilatura for better HTML scraping
import trafilatura

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EnhancedScraper:
    """
    Enhanced scraping capabilities using trafilatura and requests with advanced browser emulation.
    This provides better compatibility with websites that might block basic scrapers.
    """
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/122.0.2365.92',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0'
        ]
        self.accept_headers = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ]
        self.session = self._create_session()
        
    def _create_session(self):
        """Create a new session with cookies and headers that mimic a real browser"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': random.choice(self.accept_headers),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        })
        return session
    
    def reset_session(self):
        """Reset the session with new headers"""
        self.session = self._create_session()
        
    def visit_homepage(self):
        """Visit the homepage to establish cookies and warm up the session"""
        try:
            logger.debug("Visiting homepage to establish session")
            response = self.session.get(
                'https://new4.scloud.ninja/',
                timeout=30
            )
            if response.status_code == 200:
                logger.debug("Successfully visited homepage")
                # Add a small delay to mimic human behavior
                time.sleep(random.uniform(0.5, 1.2))
                return True
            else:
                logger.warning(f"Failed to visit homepage: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Error visiting homepage: {str(e)}")
            return False
            
    def fetch_html(self, url, max_retries=3):
        """
        Fetch HTML content from a URL with retries.
        
        Args:
            url (str): The URL to fetch
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: HTML content of the page
        """
        # First try trafilatura which has better anti-blocking capabilities
        try:
            logger.debug(f"Fetching {url} with trafilatura")
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                # trafilatura.fetch_url returns None on failure
                return downloaded
            logger.debug("Trafilatura fetch failed, falling back to requests")
        except Exception as e:
            logger.warning(f"Trafilatura error: {str(e)}")
        
        # Fall back to requests if trafilatura fails
        for attempt in range(max_retries):
            try:
                # Reset session and update headers on retries
                if attempt > 0:
                    logger.debug(f"Retry attempt {attempt+1} for {url}")
                    self.reset_session()
                    self.visit_homepage()
                    
                response = self.session.get(
                    url,
                    timeout=30,
                    headers={
                        'User-Agent': random.choice(self.user_agents),
                        'Accept': random.choice(self.accept_headers),
                        'Referer': 'https://new4.scloud.ninja/'
                    }
                )
                
                # Check for success
                if response.status_code == 200:
                    return response.text
                
                # If we get a 403 or other error, wait before retrying
                logger.warning(f"HTTP {response.status_code} for {url} on attempt {attempt+1}")
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.warning(f"Error fetching {url} on attempt {attempt+1}: {str(e)}")
                time.sleep(random.uniform(1.0, 3.0))
                
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return ""
    
    def search(self, query):
        """
        Perform a search query on scloud.ninja.
        
        Args:
            query (str): The search query
            
        Returns:
            str: HTML content of the search results page
        """
        # First check for cached results
        try:
            cache_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
            if not os.path.exists(cache_folder):
                os.makedirs(cache_folder)
                
            # Create a safe filename from the search query
            safe_query = ''.join(c if c.isalnum() else '_' for c in query)
            cache_file = os.path.join(cache_folder, f'search_{safe_query}.html')
            
            # Check if we have a fresh cache file (less than 1 hour old)
            cache_time = 60 * 60  # 1 hour
            if os.path.exists(cache_file):
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < cache_time:
                    logger.debug(f"Using cached search results for: {query}")
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return f.read()
        except Exception as cache_error:
            logger.warning(f"Cache error (non-critical): {str(cache_error)}")
            
        # Visit home page first to establish session
        self.visit_homepage()
        
        # Use direct URL approach first
        search_url = f"https://new4.scloud.ninja/search?q={urllib.parse.quote(query)}"
        logger.debug(f"Fetching search results from: {search_url}")
        html = self.fetch_html(search_url)
        
        if not html:
            # Fall back to token approach if direct search fails
            logger.debug("Direct search failed, trying token approach")
            try:
                # Get search token
                token_url = 'https://new4.scloud.ninja/get-search-token'
                token_data = f'search_query={urllib.parse.quote(query)}'
                
                token_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://new4.scloud.ninja',
                    'Referer': 'https://new4.scloud.ninja/',
                }
                
                token_response = self.session.post(
                    token_url,
                    data=token_data,
                    headers=token_headers,
                    allow_redirects=False,
                    timeout=30
                )
                
                if token_response.status_code == 302:
                    location_header = token_response.headers.get('location')
                    if location_header and 'token=' in location_header:
                        token = location_header.split('token=')[1]
                        logger.debug(f"Got search token: {token}")
                        
                        # Fetch results with token
                        results_url = f'https://new4.scloud.ninja/?token={token}'
                        html = self.fetch_html(results_url)
                    else:
                        logger.warning("Failed to extract token from Location header")
                else:
                    logger.warning(f"Expected 302 redirect for token, got {token_response.status_code}")
            except Exception as token_error:
                logger.exception(f"Token approach failed: {str(token_error)}")
        
        # Save to cache if we got results
        if html:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.debug(f"Cached search results for: {query}")
            except Exception as cache_error:
                logger.warning(f"Failed to cache search results: {str(cache_error)}")
                
        return html or "<html><body></body></html>"
        
    def get_file_details(self, file_url):
        """
        Get file details from a file page.
        
        Args:
            file_url (str): The URL of the file page
            
        Returns:
            dict: Dictionary containing downloadLink, filename, and size
        """
        # Check cache first
        file_id = file_url.split('/')[-1]
        try:
            cache_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
            cache_file = os.path.join(cache_folder, f'file_{file_id}.json')
            cache_time = 60 * 60 * 24  # 24 hours
            
            if not os.path.exists(cache_folder):
                os.makedirs(cache_folder)
                
            if os.path.exists(cache_file):
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < cache_time:
                    logger.debug(f"Using cached file details for: {file_id}")
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as cache_error:
            logger.warning(f"Cache error (non-critical): {str(cache_error)}")
            
        # Warm up the session
        self.visit_homepage()
        
        # Fetch the file page
        logger.debug(f"Fetching file details from: {file_url}")
        html = self.fetch_html(file_url)
        
        if not html:
            logger.error(f"Failed to fetch HTML for: {file_url}")
            return {
                "downloadLink": "",
                "filename": "Error fetching file - no response",
                "size": "Unknown"
            }
            
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract download link
        download_link = ""
        download_selectors = [
            'a.block',                         # Primary selector
            'a[href*="download"]',             # Any link with 'download' in href
            'a.bg-blue-400',                   # Potentially styled download button
            'a[href*="file"]',                 # Any link with 'file' in href
            'a.btn',                           # Generic button class
            'a.px-4',                          # Padding class often used for buttons
            'a.py-2',                          # Padding class often used for buttons
            'a.rounded',                       # Rounded corners often used for buttons
            'a.text-center'                    # Center-aligned text often used for buttons
        ]
        
        for selector in download_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Check if this might be a download link
                    href = element.get('href')
                    if href and ('download' in href.lower() or 'file' in href.lower()):
                        download_link = href
                        break
                if download_link:
                    break
            except Exception as selector_error:
                logger.warning(f"Error with selector '{selector}': {str(selector_error)}")
                
        # Extract filename
        filename = "Unknown"
        filename_element = None
        filename_selectors = [
            'div.space-y-4.mb-6 > div:nth-child(1) > p',
            'div.mb-6 p',
            'p.text-lg',
            'h1',
            'h2',
            'div.file-name',
            'p:contains("Name")',
            'p:contains("File:")'
        ]
        
        for selector in filename_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    filename = element.text.strip()
                    filename_element = element
                    break
            except Exception as selector_error:
                logger.warning(f"Error with selector '{selector}': {str(selector_error)}")
                
        # Extract file size
        size = "Unknown"
        size_selectors = [
            'div.space-y-4.mb-6 > div:nth-child(2) > p',
            'span.text-sm',
            'div.file-size',
            'p:contains("Size")',
            'p:contains("size:")',
            'p:contains("MB")',
            'p:contains("GB")'
        ]
        
        for selector in size_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    size = element.text.strip()
                    break
            except Exception as selector_error:
                logger.warning(f"Error with selector '{selector}': {str(selector_error)}")
                
        # Fallback: try to find size in any paragraph after the filename
        if size == "Unknown" and filename_element:
            try:
                next_p = filename_element.find_next('p')
                if next_p:
                    size = next_p.text.strip()
            except Exception as next_p_error:
                logger.warning(f"Error finding next paragraph: {str(next_p_error)}")
                
        # Build result
        result = {
            "downloadLink": download_link,
            "filename": filename,
            "size": size
        }
        
        # Save to cache
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f)
            logger.debug(f"Cached file details for: {file_id}")
        except Exception as cache_error:
            logger.warning(f"Failed to cache file details: {str(cache_error)}")
            
        return result

# Create a global scraper instance
enhanced_scraper = EnhancedScraper()

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
        # Get the file ID from the query parameters
        file_id = request.args.get('id')
        
        if not file_id:
            logger.error("No file ID provided")
            # Return empty result with valid structure instead of error code
            return jsonify({
                "downloadLink": "",
                "filename": "No file ID provided",
                "size": "Unknown"
            }), 200, {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            }
        
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
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache'
        }
        
    except Exception as e:
        logger.exception("Failed to fetch data")
        # Return empty result with valid structure instead of error code
        return jsonify({
            "downloadLink": "",
            "filename": "Error fetching file",
            "size": "Server error"
        }), 200, {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
        }

def fetch_html_link(link):
    """
    Fetches and parses the HTML from the provided link to extract download information.
    
    Args:
        link (str): The URL of the file page to scrape
        
    Returns:
        dict: Dictionary containing downloadLink, filename, and size
    """
    logger.debug(f"Fetching HTML from: {link}")
    
    # Use enhanced scraper to get file details
    # The scraper handles caching internally
    return enhanced_scraper.get_file_details(link)

@app.route('/api/search', methods=['GET'])
def search_files():
    """
    GET endpoint that accepts a search query and returns search results
    from scloud.ninja website.
    """
    try:
        # Get the search query from the request parameters
        search_query = request.args.get('search')
        
        # Validate search query
        if not search_query:
            logger.warning("Empty search query provided")
            return jsonify([]), 200, {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            }
            
        decoded_query = urllib.parse.unquote(search_query)
        logger.debug(f"GET /api/search with search=\"{decoded_query}\"")
        
        # Fetch search results
        html = fetch_search_results(decoded_query)
        
        # Parse and extract results - will return empty list if HTML is empty or invalid
        results = parse_search_results(html)
        
        # Return JSON response with appropriate headers - always return 200 with empty list for no results
        # This prevents 500 errors from being displayed to the user on cloud platforms
        return jsonify(results), 200, {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache'
        }
        
    except Exception as e:
        logger.exception("Failed to fetch search results")
        # Return empty list instead of error to avoid 500 status code
        return jsonify([]), 200, {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
        }

def fetch_search_results(search_query):
    """
    Fetches search results from scloud.ninja using enhanced scraping techniques.
    
    Args:
        search_query (str): The search query
        
    Returns:
        str: HTML content of the search results page
    """
    logger.debug(f"Fetching search results for: {search_query}")
    
    # Use the enhanced scraper to fetch search results
    # The scraper handles caching internally, so we don't need to handle it here
    return enhanced_scraper.search(search_query)

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
    app.run(host="0.0.0.0", port=5000, debug=True)