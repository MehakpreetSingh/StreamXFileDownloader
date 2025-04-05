import os
import logging
import requests
import json
import re
import time
import random
import datetime
from flask import Blueprint, request, jsonify
from bs4 import BeautifulSoup
import urllib.parse
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Constants
SEARCH_URL = "https://new4.scloud.ninja/get-search-token"
SEARCH_RESULTS_URL = "https://new4.scloud.ninja/?token="

# User agent rotation list
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/122.0.2365.92',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0'
]

# Accept headers rotation list
ACCEPT_HEADERS = [
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
]

# Get random user agent for this session
USER_AGENT = random.choice(USER_AGENTS)

# Set session for reuse
session = requests.Session()

# Cache for anime list data
anime_list_cache = {
    'data': None,
    'timestamp': None,
    'expiry': 14400  # Cache expiry in seconds (4 hours)
}

@api_bp.route('/search', methods=['GET'])
def search():
    """Search for files on scloud.ninja."""
    try:
        # Get search query from request
        search_query = request.args.get('search', '')
        if not search_query:
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Searching for: {search_query}")

        # Step 1: Get Search Token
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://new4.scloud.ninja',
            'Referer': 'https://new4.scloud.ninja/',
            'User-Agent': USER_AGENT,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8',
            'Cookie': 'cf_clearance=F7Sv0K2A.u4bWuvR1BQI0WEDo0vPy17rmiMubuJl7mE-1743607723-1.2.1.1-Ds1moOAkHL1LthKerBsN54LCyTJoTc6wi0pAvPntD79_WjwgV3NM8MYM826l3b3VNp9rSyWm.wrqUgldIacaA38E8gA2IubI2Ty2bxdMXiKANqI6sJZghQiTjmh9KdgjMryJU4NlfNYAe4vhuL_zqOUzWayRFomzEEjLiNe77b5uM0.M44HVIftkQnRBEIRp7hjKoKYjWCAuWwsqhMV2QvA3jHcncH7MFbxX_487z5DHQiqwCow8zcxgLIWjhakvU5i6.U_jG5JeRI1qDLVJ1D1jsyfJlKZrh0JnPiEMd3cOkia1v5vNW5GIF4jGoAUpdbzJyzRxS7lHq5.lXvoCn7nrjO8TsT00ZED4XoZ2B2gNStMhyPRU9JPzk_XoQK7x',
            'Priority': 'u=0, i',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        }

        # Prepare form data
        form_data = f"search_query={urllib.parse.quote(search_query)}"

        # Make POST request to get token
        token_response = session.post(
            SEARCH_URL,
            data=form_data,
            headers=headers,
            allow_redirects=False,
        )

        # Check if response contains redirect with token
        if token_response.status_code != 302:
            logger.error(f"Invalid response from token request: {token_response.status_code}")
            return jsonify({"error": "Failed to get search token"}), 500

        # Extract token from Location header
        location_header = token_response.headers.get('location', '')
        token_match = re.search(r'token=([a-f0-9\-]+)', location_header)

        if not token_match:
            logger.error("Failed to extract token from redirect URL")
            return jsonify({"error": "Failed to extract search token"}), 500

        token = token_match.group(1)
        logger.debug(f"Extracted token: {token}")

        # Step 2: Fetch search results with token
        results_url = f"{SEARCH_RESULTS_URL}{token}"
        results_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': USER_AGENT,
            'Referer': 'https://new4.scloud.ninja/'
        }

        results_response = session.get(results_url, headers=results_headers)

        if results_response.status_code != 200:
            logger.error(f"Failed to fetch search results: {results_response.status_code}")
            return jsonify({"error": "Failed to fetch search results"}), 500

        # Parse HTML response
        results = parse_search_results(results_response.text)

        return jsonify(results)

    except Exception as e:
        logger.exception(f"Search error: {str(e)}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@api_bp.route('/download', methods=['GET'])
def download():
    """Get download link for a specific file."""
    try:
        # Get file ID from request
        file_id = request.args.get('id', '')
        if not file_id:
            logger.error("No file ID provided")
            # Return empty result with valid structure instead of error code
            return jsonify({
                "downloadLink": "",
                "filename": "No file ID provided",
                "size": "Unknown"
            }), 200

        logger.debug(f"GET /api/download with id={file_id}")

        # Form the URL with the base URL and the file ID
        file_url = f"https://new4.scloud.ninja/file/{file_id}"

        # Fetch file details
        result = fetch_file_details(file_url)

        # Return JSON response with appropriate headers
        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"Download error: {str(e)}")
        # Return empty result with valid structure instead of error code
        return jsonify({
            "downloadLink": "",
            "filename": "Error fetching file",
            "size": "Server error"
        }), 200

def fetch_file_details(link):
    """
    Fetches and parses the HTML from the provided link to extract download information.

    Args:
        link (str): The URL of the file page to scrape

    Returns:
        dict: Dictionary containing downloadLink, filename, and size
    """
    logger.debug(f"Fetching file details from: {link}")

    try:
        # Set timeout for requests
        timeout = 30  # seconds

        # Get random user agent and accept header
        random_user_agent = random.choice(USER_AGENTS)
        random_accept = random.choice(ACCEPT_HEADERS)

        try:
            # Create a session for more reliable connections
            file_session = requests.Session()

            # First get the homepage to establish a session with cookies
            home_headers = {
                'User-Agent': random_user_agent,
                'Accept': random_accept,
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            file_session.get('https://new4.scloud.ninja/', headers=home_headers, timeout=timeout)

            # Add a small random delay to mimic human behavior
            time.sleep(random.uniform(0.5, 1.2))
        except Exception as e:
            logger.warning(f"Error warming up session (continuing): {str(e)}")
            # Continue anyway with our existing session
            file_session = session

        # Make robust request headers
        headers = {
            'User-Agent': random_user_agent,
            'Accept': random_accept,
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://new4.scloud.ninja/',
            'Cache-Control': 'no-cache'
        }

        # Try to get the file details
        response = file_session.get(link, headers=headers, timeout=timeout)

        # Handle HTTP status codes
        if response.status_code != 200:
            logger.error(f"Failed to fetch file details: HTTP {response.status_code}")

            # Try a fallback approach with a different user agent and URL structure
            try:
                # Wait a moment before retry
                time.sleep(random.uniform(1.0, 2.0))

                # Try the alternative URL structure
                fallback_url = f"https://new3.scloud.ninja/f/{link.split('/')[-1]}"
                fallback_headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': random.choice(ACCEPT_HEADERS),
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Referer': 'https://new3.scloud.ninja/'
                }

                fallback_response = requests.get(fallback_url, headers=fallback_headers, timeout=timeout)

                if fallback_response.status_code == 200:
                    response = fallback_response
                    logger.debug("Fallback approach succeeded")
                else:
                    logger.error(f"Fallback approach also failed: HTTP {fallback_response.status_code}")
                    return {
                        "downloadLink": "",
                        "filename": "Error fetching file - server restriction",
                        "size": "Unknown"
                    }
            except Exception as fallback_error:
                logger.exception(f"Fallback approach failed: {str(fallback_error)}")
                return {
                    "downloadLink": "",
                    "filename": "Error fetching file",
                    "size": "Unknown"
                }

        html = response.text

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Try multiple selectors for downloading links
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
            '.title-container span',
            'div.file-name',
            'title'
        ]

        for selector in filename_selectors:
            filename_element = soup.select_one(selector)
            if filename_element and filename_element.text.strip():
                filename = filename_element.text.strip()
                if 'scloud' not in filename.lower():  # Skip if it's just the site name
                    break

        # Try multiple selectors for file size
        size_selectors = [
            'div.space-y-4.mb-6 > div:nth-child(2) > p',
            'span.text-sm',
            'div.file-size',
            'span.inline-block',
            '.size'
        ]

        for selector in size_selectors:
            size_element = soup.select_one(selector)
            if size_element and size_element.text.strip():
                size = size_element.text.strip()
                break

        # If still not found, try to find text containing common file size patterns
        if size == "Unknown":
            size_pattern = re.compile(r'(\d+(\.\d+)?\s*(KB|MB|GB|TB))', re.IGNORECASE)
            text_elements = soup.find_all(text=True)

            for text in text_elements:
                match = size_pattern.search(text)
                if match:
                    size = match.group(0)
                    break

        # If we still don't have a download link, generate one based on file ID
        if not download_link:
            file_id = link.split('/')[-1]
            download_link = f"https://new4.scloud.ninja/dl/{file_id}"
            logger.warning(f"Generated fallback download link for file ID: {file_id}")

        logger.debug(f"Extracted download link: {download_link}")
        logger.debug(f"Extracted filename: {filename}")
        logger.debug(f"Extracted size: {size}")

        # Return the results
        return {
            "downloadLink": download_link,
            "filename": filename,
            "size": size
        }

    except requests.RequestException as e:
        logger.exception(f"Request exception: {str(e)}")
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

def parse_search_results(html_content):
    """Parse the search results HTML and extract file information."""
    try:
        result = []
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all elements that might be file containers
        file_containers = soup.select('.file-item') or soup.select('.file-container') or soup.select('.grid a[href]')

        # If no containers found, try a more general approach
        if not file_containers:
            file_containers = soup.select('a[href]')

        for container in file_containers:
            # Get the link (either the container itself or a child)
            link_elem = container if container.name == 'a' else container.select_one('a[href]')

            if not link_elem or not link_elem.get('href'):
                continue

            href = link_elem.get('href')

            # Try multiple selectors for title
            title_selectors = [
                '.title-container span',
                '.file-name',
                'h3',
                'p.text-lg',
                'strong',
                '.name'
            ]

            title_elem = None
            for selector in title_selectors:
                title_elem = link_elem.select_one(selector) or container.select_one(selector)
                if title_elem:
                    break

            # Try multiple selectors for size
            size_selectors = [
                'span.inline-block',
                '.file-size',
                '.size',
                '.text-gray-500',
                'span.text-sm'
            ]

            size_elem = None
            for selector in size_selectors:
                size_elem = link_elem.select_one(selector) or container.select_one(selector)
                if size_elem:
                    break

            # Skip if we couldn't find title or size
            if not title_elem or not size_elem:
                continue

            title = title_elem.text.strip()
            size = size_elem.text.strip()

            # Extract file ID from href
            # Check if there's a file ID pattern in the URL (uuid style)
            uuid_pattern = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', href)
            if uuid_pattern:
                file_id = uuid_pattern.group(1)
            else:
                # Fall back to the last segment of the path
                file_id = href.split('/')[-1] if href else ""

            if title and size and file_id:
                result.append({
                    "name": title,
                    "size": size,
                    "link": file_id
                })

        # If no results were found with our selectors, try a more aggressive approach
        if not result:
            # Look for any elements with text that might be movie titles and nearby elements with size information
            title_candidates = soup.select('h3, h4, strong, b, span.text-lg, div.text-lg')

            for title_elem in title_candidates:
                title = title_elem.text.strip()

                # Skip very short or common text
                if len(title) < 5 or title.lower() in ['file', 'size', 'download', 'scloud', 'results']:
                    continue

                # Try to find a nearby size element
                size_elem = None
                next_elem = title_elem.find_next(['span', 'div', 'p'])

                if next_elem:
                    size_text = next_elem.text.strip()
                    size_match = re.search(r'\d+(\.\d+)?\s*(KB|MB|GB|TB)', size_text, re.IGNORECASE)

                    if size_match:
                        size = size_match.group(0)

                        # Look for a nearby link
                        link_elem = title_elem.find_parent('a') or title_elem.find_previous('a') or title_elem.find_next('a')

                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            uuid_pattern = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', href)

                            if uuid_pattern:
                                file_id = uuid_pattern.group(1)

                                result.append({
                                    "name": title,
                                    "size": size,
                                    "link": file_id
                                })

        # Log the number of results found
        logger.debug(f"Found {len(result)} search results")
        return result
    except Exception as e:
        logger.exception(f"Error parsing search results: {str(e)}")
        return []

@api_bp.route('/anime/list', methods=['GET'])
def get_anime_list():
    """Get list of all anime from tokyoinsider"""
    try:
        # Get query parameters
        letter = request.args.get('letter')
        random_select = request.args.get('random', 'false').lower() == 'true'
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        base_url = "https://www.tokyoinsider.com"
        list_url = f"{base_url}/anime/list"
        
        # Check if we have a valid cache
        current_time = datetime.datetime.now()
        cache_valid = (
            anime_list_cache['data'] is not None and 
            anime_list_cache['timestamp'] is not None and
            (current_time - anime_list_cache['timestamp']).total_seconds() < anime_list_cache['expiry'] and
            not force_refresh
        )
        
        if cache_valid:
            logger.debug("Using cached anime list data")
            anime_list = anime_list_cache['data']
        else:
            logger.debug("Fetching fresh anime list data")
            response = session.get(list_url, headers={'User-Agent': USER_AGENT})
            soup = BeautifulSoup(response.text, 'html.parser')

            anime_list = []

            # Find all anime entries (both c_h2 and c_h2b classes)
            anime_entries = soup.find_all(class_=['c_h2', 'c_h2b'])

            for entry in anime_entries:
                link = entry.find('a')
                if link:
                    title = link.text.strip()
                    href = link.get('href')
                    if href:
                        # Extract anime poster URL from the page if available
                        poster_url = None
                        img = entry.find('img')
                        if img and img.get('src') and not img.get('alt') == 'Completed':
                            poster_url = img.get('src')
                            if not poster_url.startswith('http'):
                                poster_url = f"{base_url}{poster_url}"
                        
                        anime_list.append({
                            'title': title,
                            'url': base_url + href,
                            'status': 'Completed' if entry.find('img', alt='Completed') else 'Airing',
                            'poster_url': poster_url
                        })
                
            # Update the cache
            anime_list_cache['data'] = anime_list
            anime_list_cache['timestamp'] = current_time

        # Filter by first letter if specified
        if letter and letter != 'all' and letter != '0-9':
            anime_list = [anime for anime in anime_list if anime['title'].startswith(letter)]
        elif letter == '0-9':
            # Filter for titles starting with numbers
            anime_list = [anime for anime in anime_list if anime['title'][0].isdigit()]
            
        # Return random selection if requested
        if random_select:
            if anime_list:
                import random
                random_count = min(20, len(anime_list))  # Limit to 20 random anime
                anime_list = random.sample(anime_list, random_count)
            
        return jsonify(anime_list)
    except Exception as e:
        logger.exception(f"Error fetching anime list: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/anime/details', methods=['GET'])
def get_anime_details_v2():
    """Get details for a specific anime (alternative implementation)"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400

        response = session.get(url, headers={'User-Agent': USER_AGENT})
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract basic info
        info = {
            'title': 'Unknown Title',
            'creator': 'Unknown Creator',
            'genres': [],
            'summary': 'No summary available.',
            'episodes': []
        }

        # Get title from the Title(s) row (first entry before newline)
        title_row = soup.find('tr', class_='c_h2')
        if title_row and title_row.find('td', text='Title(s):'):
            try:
                titles = title_row.find_all('td')[1].get_text().split('\n')
                if len(titles) > 1:
                    info['title'] = titles[1].strip()
            except (IndexError, AttributeError) as e:
                logger.warning(f"Error parsing title: {str(e)}")

        # Fall back to h1 or page title if no title found
        if info['title'] == 'Unknown Title':
            h1 = soup.find('h1')
            if h1:
                info['title'] = h1.text.strip()
            else:
                title_tag = soup.find('title')
                if title_tag:
                    info['title'] = title_tag.text.replace('TokyoInsider -', '').strip()

        # Get poster image
        poster_elem = soup.select_one('.a_img')
        if poster_elem and poster_elem.get('src'):
            info['poster_url'] = poster_elem['src'] if poster_elem['src'].startswith('http') else f"https://www.tokyoinsider.com{poster_elem['src']}"

        # Get creator
        creator_elem = soup.select_one('.c_h2b a[href*="search?c="]')
        if creator_elem:
            info['creator'] = creator_elem.text.strip()

        # Get genres
        genre_links = soup.select('.c_h2 a[href*="search?g="]')
        if genre_links:
            info['genres'] = [a.text.strip() for a in genre_links]

        # Get summary
        summary_elem = soup.select_one('.c_h2:last-child td:nth-child(2)')
        if summary_elem:
            info['summary'] = summary_elem.text.strip()

        # Extract episodes
        episodes = []
        episode_divs = soup.find_all(class_=['episode c_h2', 'episode c_h2b'])
        for div in episode_divs:
            try:
                link = div.find('a', class_='download-link')
                if link and link.get('href'):
                    ep_text = link.find('strong')
                    ep_num = ep_text.text if ep_text else 'Unknown Episode'
                    episodes.append({
                        'number': ep_num,
                        'url': 'https://www.tokyoinsider.com' + link['href'] if not link['href'].startswith('http') else link['href']
                    })
            except (AttributeError, KeyError) as e:
                logger.warning(f"Error parsing episode: {str(e)}")
                continue

        # If no episodes found with class, try a more general approach
        if not episodes:
            for div in soup.find_all(['div', 'tr'], class_=['c_h2', 'c_h2b']):
                # Check if "Episode" text is in the div
                if 'episode' in div.text.lower():
                    links = div.find_all('a')
                    for link in links:
                        if link.get('href') and 'episode' in link.text.lower():
                            ep_match = re.search(r'Episode\s+(\d+)', link.text, re.IGNORECASE)
                            ep_num = ep_match.group(0) if ep_match else 'Episode'
                            episodes.append({
                                'number': ep_num,
                                'url': 'https://www.tokyoinsider.com' + link['href'] if not link['href'].startswith('http') else link['href']
                            })

        info['episodes'] = episodes

        return jsonify(info)
    except Exception as e:
        logger.exception(f"Error fetching anime details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/episode/download', methods=['GET'])
def get_episode_download_v2():
    """Get episode sources and direct download links"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400

        response = session.get(url, headers={'User-Agent': USER_AGENT})
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the inner_page div that contains the episode sources
        inner_page = soup.find(id='inner_page')
        if not inner_page:
            return jsonify({'error': 'Episode page structure not recognized'}), 404
        
        # Get the HTML content for client-side parsing
        inner_page_html = str(inner_page)
        
        # Extract all available sources from the content
        sources = []
        content_divs = inner_page.find_all(class_=['c_h2', 'c_h2b'])
        
        for div in content_divs:
            try:
                # Find all links in the div - we need both links
                links = div.find_all('a')
                if len(links) < 2:
                    continue
                
                # First link in each div is usually the comment link, second is the download link
                download_link = None
                file_name = ""
                
                for link in links:
                    href = link.get('href')
                    # Skip comment links
                    if href and '/comment' in href:
                        continue
                    # Found download link
                    if href and (
                        href.startswith('https://') and 
                        (href.endswith('.mp4') or href.endswith('.mkv') or 'dl/' in href)
                    ):
                        download_link = href
                        file_name = link.text.strip()
                        break
                
                if not download_link or not file_name:
                    continue
                
                # Extract file size and download count from file info div
                file_info = div.find(class_='finfo')
                size = ""
                downloads = "0"
                uploader = ""
                added_date = ""
                
                if file_info:
                    info_text = file_info.get_text()
                    
                    # Extract size
                    size_match = re.search(r'Size:\s*<b>([^<]+)</b>', str(file_info))
                    if size_match:
                        size = size_match.group(1)
                    
                    # Extract downloads
                    downloads_match = re.search(r'Downloads:\s*<b>([^<]+)</b>', str(file_info))
                    if downloads_match:
                        downloads = downloads_match.group(1)
                        
                    # Extract uploader
                    uploader_match = re.search(r'Uploader:\s*<b>([^<]+)</b>', str(file_info))
                    if uploader_match:
                        uploader = uploader_match.group(1)
                        
                    # Extract date
                    date_match = re.search(r'Added On:\s*<b>([^<]+)</b>', str(file_info))
                    if date_match:
                        added_date = date_match.group(1)
                
                # Add source to list
                sources.append({
                    'name': file_name,
                    'download_url': download_link,
                    'size': size,
                    'downloads': downloads,
                    'uploader': uploader,
                    'added_date': added_date
                })
            except Exception as e:
                # Log the error but continue with other sources
                logger.error(f"Error extracting source: {str(e)}")
                continue
        
        # Also try to find a direct download link for backward compatibility
        download_url = None
        if sources and len(sources) > 0:
            download_url = sources[0]['download_url']
        
        # Return both the HTML content and the sources if found
        response_data = {
            'html_content': inner_page_html,
            'sources': sources
        }
        
        if download_url:
            response_data['download_url'] = download_url
            
        return jsonify(response_data)
    except Exception as e:
        logger.exception(f"Error fetching episode download: {str(e)}")
        return jsonify({'error': str(e)}), 500