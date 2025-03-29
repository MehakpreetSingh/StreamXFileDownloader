import os
import logging
import requests
import urllib.parse
import time
import random
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
    
    try:
        # Set timeout for requests - important for cloud environments
        timeout = 30  # seconds
        
        # Generate a realistic user agent from a selection of modern browsers
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/122.0.2365.92',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0'
        ]
        
        import random
        random_user_agent = random.choice(user_agents)
        
        # Create a dictionary of different accept headers for variation
        accept_headers = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ]
        random_accept = random.choice(accept_headers)
        
        # First, try to visit the homepage to warm up the session
        try:
            # Create a session for more reliable connections
            session = requests.Session()
            
            # First get the homepage to establish a session with cookies
            home_headers = {
                'User-Agent': random_user_agent,
                'Accept': random_accept,
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            session.get('https://new4.scloud.ninja/', headers=home_headers, timeout=timeout)
            
            # Add a small random delay to mimic human behavior
            time.sleep(random.uniform(0.5, 1.2))
        except Exception as e:
            logger.warning(f"Error visiting homepage (continuing anyway): {str(e)}")
            # Continue anyway, as this is just to warm up the session
            session = requests.Session()  # Create a new session if the first one failed
        
        # Make robust request headers for the file page that mimic a real browser
        headers = {
            'User-Agent': random_user_agent,
            'Accept': random_accept,
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://new4.scloud.ninja/',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Option to disable SSL verification if needed
        verify_ssl = True
        
        # Try to get the file details
        response = session.get(link, headers=headers, timeout=timeout, verify=verify_ssl)
        
        # Handle HTTP status codes without raising exceptions
        if response.status_code != 200:
            logger.error(f"Failed to fetch file details: HTTP {response.status_code}")
            
            # Try a fallback approach with a different user agent and headers
            try:
                # Wait a moment before retry
                time.sleep(random.uniform(1.0, 2.0))
                
                fallback_user_agent = random.choice(user_agents)
                fallback_headers = {
                    'User-Agent': fallback_user_agent,
                    'Accept': random_accept,
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Referer': 'https://new4.scloud.ninja/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin'
                }
                
                # Create a fresh session
                fallback_session = requests.Session()
                fallback_response = fallback_session.get(link, headers=fallback_headers, timeout=timeout, verify=verify_ssl)
                
                if fallback_response.status_code == 200:
                    response = fallback_response
                    logger.debug("Fallback approach for file details succeeded")
                else:
                    logger.error(f"Fallback approach also failed: HTTP {fallback_response.status_code}")
                    return {
                        "downloadLink": "",
                        "filename": "Error fetching file - server restriction",
                        "size": "Unknown"
                    }
            except Exception as fallback_error:
                logger.exception(f"Fallback approach failed with error: {str(fallback_error)}")
                return {
                    "downloadLink": "",
                    "filename": "Error fetching file",
                    "size": "Unknown"
                }
        
        html = response.text
        
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try multiple selectors for downloading links - more robust approach
        download_link = ""
        download_selectors = [
            'a.block',                         # Primary selector
            'a[href*="download"]',             # Any link with 'download' in href
            'a.bg-blue-400',                   # Potentially styled download button
            'a[href*="file"]',                 # Any link with 'file' in href
            'a.btn'                            # Generic button class
        ]
        
        for selector in download_selectors:
            download_element = soup.select_one(selector)
            if download_element and download_element.get('href'):
                download_link = download_element.get('href')
                break
        
        # Extract filename and size with multiple fallback selectors
        filename = "Unknown"
        size = "Unknown"
        
        # Try multiple selectors for filename
        filename_selectors = [
            'div.space-y-4.mb-6 > div:nth-child(1) > p',
            'div.mb-6 p',
            'p.text-lg',
            'h1',
            'h2',
            'div.file-name'
        ]
        
        for selector in filename_selectors:
            filename_element = soup.select_one(selector)
            if filename_element and filename_element.text.strip():
                filename = filename_element.text.strip()
                break
        
        # Try multiple selectors for file size
        size_selectors = [
            'div.space-y-4.mb-6 > div:nth-child(2) > p',
            'span.text-sm',
            'div.file-size',
            'p:contains("Size")'
        ]
        
        for selector in size_selectors:
            size_element = soup.select_one(selector)
            if size_element and size_element.text.strip():
                size = size_element.text.strip()
                break
                
        # If still not found, try to find a paragraph that might contain size information
        if size == "Unknown" and filename != "Unknown" and 'filename_element' in locals():
            # Try to find any paragraph after the filename element
            if filename_element:
                next_p = filename_element.find_next('p')
                if next_p:
                    size = next_p.text.strip()
        
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
        
    except requests.RequestException as e:
        logger.exception(f"Request exception while fetching file details: {str(e)}")
        return {
            "downloadLink": "",
            "filename": "Error fetching file",
            "size": "Connection error"
        }
    except Exception as e:
        logger.exception(f"Error fetching file details: {str(e)}")
        return {
            "downloadLink": "",
            "filename": "Error fetching file",
            "size": "Unknown error"
        }

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
        
        # Set larger timeouts for cloud environments
        timeout = 30  # seconds
        
        # Generate a realistic user agent from a selection of modern browsers
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/122.0.2365.92',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0'
        ]
        
        import random
        random_user_agent = random.choice(user_agents)
        
        # Create a dictionary of different accept headers for variation
        accept_headers = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        ]
        random_accept = random.choice(accept_headers)
        
        # Step 1: First visit the homepage to get cookies
        try:
            home_headers = {
                'User-Agent': random_user_agent,
                'Accept': random_accept,
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Visit the homepage first to get cookies
            session.get('https://new4.scloud.ninja/', headers=home_headers, timeout=timeout)
            
            # Add a small random delay to mimic human behavior
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.warning(f"Error visiting homepage (continuing anyway): {str(e)}")
            # Continue anyway, as this is just to warm up the session
        
        # Step 2: Get Search Token
        token_url = 'https://new4.scloud.ninja/get-search-token'
        token_data = f'search_query={urllib.parse.quote(search_query)}'
        
        # Create advanced headers that mimic a real browser for the token request
        headers = {
            'Accept': random_accept,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://new4.scloud.ninja',
            'Referer': 'https://new4.scloud.ninja/',
            'User-Agent': random_user_agent,
            'Connection': 'keep-alive',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Option to disable SSL verification (not recommended but can help diagnose issues)
        verify_ssl = True
        
        # Try the first approach - direct post for token
        logger.debug("Attempting to get search token with POST request")
        try:
            # Send POST request and capture the redirect without following it
            token_response = session.post(
                token_url,
                data=token_data,
                headers=headers,
                allow_redirects=False,
                timeout=timeout,
                verify=verify_ssl
            )
            
            # Check if we got a redirect response
            if token_response.status_code != 302:
                logger.warning(f"Expected 302 redirect, got {token_response.status_code}")
                # Don't return immediately, try the fallback approach
                raise Exception(f"Unexpected status code: {token_response.status_code}")
                
            # Extract token from the Location header
            location_header = token_response.headers.get('location')
            if not location_header:
                logger.warning("No Location header in response")
                raise Exception("Missing Location header")
                
            # Extract token from redirect URL
            token_match = location_header.split('token=')
            if len(token_match) < 2:
                logger.warning(f"Failed to extract token from: {location_header}")
                raise Exception("Token extraction failed")
                
            token = token_match[1]
            logger.debug(f"Extracted Token: {token}")
            
        except Exception as token_error:
            # Fallback approach - try using GET request with the search in query params
            logger.debug(f"POST token approach failed: {str(token_error)}. Trying fallback approach...")
            try:
                # Try a different approach - direct query without token
                time.sleep(random.uniform(1.0, 2.0))  # Add a random delay
                
                # Try to get results directly using GET request
                fallback_url = f'https://new4.scloud.ninja/search?q={urllib.parse.quote(search_query)}'
                fallback_headers = {
                    'Accept': random_accept,
                    'User-Agent': random_user_agent,
                    'Referer': 'https://new4.scloud.ninja/',
                    'Connection': 'keep-alive',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                direct_response = session.get(
                    fallback_url,
                    headers=fallback_headers,
                    timeout=timeout,
                    verify=verify_ssl
                )
                
                logger.debug(f"Fallback approach status: HTTP {direct_response.status_code}")
                return direct_response.text
                
            except Exception as fallback_error:
                logger.exception(f"Fallback approach also failed: {str(fallback_error)}")
                return "<html><body></body></html>"
        
        # If we got here, we have a valid token
        # Step 3: Fetch search results using the token
        results_url = f'https://new4.scloud.ninja/?token={token}'
        
        # New headers for the results request - slightly different from token request
        results_headers = {
            'Accept': random_accept,
            'User-Agent': random_user_agent,
            'Referer': 'https://new4.scloud.ninja/',
            'Connection': 'keep-alive',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add a small delay with randomization to ensure token processing and mimic human behavior
        time.sleep(random.uniform(0.8, 1.5))
        
        # Get the results
        final_response = session.get(
            results_url, 
            headers=results_headers, 
            timeout=timeout, 
            verify=verify_ssl
        )
        
        # Don't raise exceptions, handle status codes instead
        if final_response.status_code != 200:
            logger.error(f"Error fetching search results: HTTP {final_response.status_code}")
            return "<html><body></body></html>"
        
        return final_response.text
        
    except requests.RequestException as e:
        logger.exception(f"Request exception fetching search results: {str(e)}")
        return "<html><body></body></html>"
    except Exception as e:
        logger.exception(f"Error fetching search results: {str(e)}")
        return "<html><body></body></html>"

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
