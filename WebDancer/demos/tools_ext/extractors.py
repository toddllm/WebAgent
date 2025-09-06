"""
Content extraction tools for web pages and documents
"""

import os
import hashlib
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import time
import json

# Create artifacts directory
ARTIFACTS_DIR = Path("./runs/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def visit_and_extract(url: str, use_scraper_api: bool = True) -> Dict[str, Any]:
    """
    Visit a webpage and extract its content with fallback options
    """
    
    # Try ScraperAPI first if key is available
    scraper_key = os.getenv('SCRAPERAPI_KEY')
    if scraper_key and use_scraper_api:
        try:
            return _visit_scraperapi(url, scraper_key)
        except Exception as e:
            print(f"ScraperAPI failed for {url}: {e}, trying direct...")
    
    # Fall back to direct request with headers
    try:
        return _visit_direct(url)
    except Exception as e:
        print(f"Direct visit failed for {url}: {e}")
        return {
            'url': url,
            'success': False,
            'error': str(e),
            'content': '',
            'title': '',
            'meta': {}
        }

def _visit_scraperapi(url: str, api_key: str) -> Dict[str, Any]:
    """Visit URL using ScraperAPI"""
    from urllib.parse import urlencode
    
    params = {
        'api_key': api_key,
        'url': url,
        'render': 'true',
        'country_code': 'us'
    }
    
    proxy_url = f"http://api.scraperapi.com/?{urlencode(params)}"
    
    response = requests.get(proxy_url, timeout=60)
    response.raise_for_status()
    
    html = response.text
    extracted = extract_content(html, url)
    
    # Save HTML artifact
    html_artifact = _save_artifact(html, f"{_url_to_filename(url)}.html")
    
    return {
        'url': url,
        'success': True,
        'content': extracted['text'],
        'title': extracted['title'],
        'meta': extracted['meta'],
        'html_artifact': html_artifact,
        'method': 'scraperapi'
    }

def _visit_direct(url: str) -> Dict[str, Any]:
    """Visit URL directly with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()
    
    html = response.text
    extracted = extract_content(html, url)
    
    # Save HTML artifact
    html_artifact = _save_artifact(html, f"{_url_to_filename(url)}.html")
    
    return {
        'url': url,
        'success': True,
        'content': extracted['text'],
        'title': extracted['title'],
        'meta': extracted['meta'],
        'html_artifact': html_artifact,
        'method': 'direct'
    }

def extract_content(html: str, url: str = "") -> Dict[str, Any]:
    """
    Extract clean text content from HTML
    Uses trafilatura with BeautifulSoup fallback
    """
    
    try:
        # Try trafilatura first (best for article content)
        import trafilatura
        
        text = trafilatura.extract(
            html, 
            include_links=True, 
            include_tables=True,
            include_comments=False,
            output_format='txt'
        )
        
        if text and len(text.strip()) > 100:
            # Also extract metadata
            metadata = trafilatura.extract_metadata(html)
            
            return {
                'text': text.strip(),
                'title': metadata.title if metadata else _extract_title_bs(html),
                'meta': {
                    'author': metadata.author if metadata else None,
                    'date': metadata.date if metadata else None,
                    'description': metadata.description if metadata else None,
                    'sitename': metadata.sitename if metadata else None,
                    'url': url,
                    'extractor': 'trafilatura'
                }
            }
    except ImportError:
        print("Trafilatura not available, using BeautifulSoup fallback")
    except Exception as e:
        print(f"Trafilatura extraction failed: {e}, using BeautifulSoup fallback")
    
    # Fallback to BeautifulSoup
    return _extract_content_bs(html, url)

def _extract_content_bs(html: str, url: str = "") -> Dict[str, Any]:
    """Extract content using BeautifulSoup fallback"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {
            'text': 'Content extraction failed: BeautifulSoup not available',
            'title': 'Extraction Error',
            'meta': {'extractor': 'none', 'url': url}
        }
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Extract title
    title = _extract_title_bs(html)
    
    # Extract main content (try common content selectors)
    content_selectors = [
        'article', 'main', '.content', '#content', 
        '.post', '.entry', '.article-body', '.story-body'
    ]
    
    content = None
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            content = elements[0]
            break
    
    # If no specific content area found, use body
    if content is None:
        content = soup.find('body') or soup
    
    # Extract text
    text = content.get_text(separator='\n', strip=True)
    
    # Clean up text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n'.join(lines)
    
    return {
        'text': text,
        'title': title,
        'meta': {
            'url': url,
            'extractor': 'beautifulsoup'
        }
    }

def _extract_title_bs(html: str) -> str:
    """Extract title using BeautifulSoup"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Try h1 as fallback
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Unknown Title"
    except:
        return "Unknown Title"

def _save_artifact(content: str, filename: str) -> Dict[str, str]:
    """Save content as artifact and return metadata"""
    
    # Create hash-based filename to avoid duplicates
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    timestamp = int(time.time())
    
    safe_filename = f"{timestamp}_{content_hash}_{filename}"
    artifact_path = ARTIFACTS_DIR / safe_filename
    
    with open(artifact_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {
        'path': str(artifact_path),
        'filename': safe_filename,
        'size': len(content),
        'hash': content_hash
    }

def _url_to_filename(url: str) -> str:
    """Convert URL to safe filename"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.replace('/', '_').replace('\\', '_')
    
    filename = f"{domain}{path}"
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Truncate if too long
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

# Jina Reader integration (if API key is available)
def extract_with_jina(url: str) -> Dict[str, Any]:
    """Extract content using Jina Reader API"""
    jina_key = os.getenv('JINA_API_KEY')
    if not jina_key:
        raise ValueError("JINA_API_KEY not available")
    
    headers = {
        'Authorization': f'Bearer {jina_key}',
        'Content-Type': 'application/json'
    }
    
    # Use Jina Reader endpoint
    reader_url = f"https://r.jina.ai/{url}"
    
    response = requests.get(reader_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    content = response.text
    
    # Save artifact
    artifact = _save_artifact(content, f"{_url_to_filename(url)}_jina.txt")
    
    return {
        'url': url,
        'success': True,
        'content': content,
        'title': _extract_title_from_content(content),
        'meta': {
            'extractor': 'jina',
            'url': url
        },
        'artifact': artifact
    }

def _extract_title_from_content(content: str) -> str:
    """Extract title from content text"""
    lines = content.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and len(line) > 10 and len(line) < 200:
            return line
    return "Unknown Title"

# Test function
if __name__ == "__main__":
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"Testing content extraction from: {test_url}")
    
    result = visit_and_extract(test_url, use_scraper_api=False)
    
    if result['success']:
        print(f"Title: {result['title']}")
        print(f"Content length: {len(result['content'])} chars")
        print(f"Method: {result['method']}")
        print(f"Artifact saved: {result.get('html_artifact', {}).get('path', 'None')}")
        print(f"Preview: {result['content'][:200]}...")
    else:
        print(f"Extraction failed: {result['error']}")