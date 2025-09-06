"""
Free search tools with paid API fallbacks
Uses DuckDuckGo by default, upgrades to SerpAPI/Serper when keys are available
"""

import os
import requests
from typing import List, Dict, Any
import json
from urllib.parse import urlencode

def search_web(query: str, num_results: int = 8) -> List[Dict[str, Any]]:
    """
    Search the web for text results
    Priority: Exa.ai > Serper API > SerpAPI > DuckDuckGo (free)
    """
    
    # Try Exa.ai first (best for AI research)
    exa_key = os.getenv('EXA_API_KEY')
    if exa_key:
        try:
            print(f"🔍 Using Exa.ai neural search for: {query}")
            return _search_exa(query, num_results, exa_key)
        except Exception as e:
            print(f"Exa.ai search failed: {e}, falling back...")
    
    # Try Tavily AI (free tier available)
    tavily_key = os.getenv('TAVILY_API_KEY')
    if tavily_key:
        try:
            print(f"🔍 Using Tavily AI search for: {query}")
            return _search_tavily(query, num_results, tavily_key)
        except Exception as e:
            print(f"Tavily AI search failed: {e}, falling back...")
    
    # Try Serper API (Google Search)
    serper_key = os.getenv('GOOGLE_SEARCH_KEY') or os.getenv('SERPER_API_KEY')
    if serper_key:
        try:
            print(f"🔍 Using Google Search (Serper) for: {query}")
            return _search_serper(query, num_results, serper_key)
        except Exception as e:
            print(f"Serper API failed: {e}, falling back...")
    
    # Try SerpAPI
    serpapi_key = os.getenv('SERPAPI_API_KEY')
    if serpapi_key:
        try:
            print(f"🔍 Using Google Search (SerpAPI) for: {query}")
            return _search_serpapi(query, num_results, serpapi_key)
        except Exception as e:
            print(f"SerpAPI failed: {e}, falling back...")
    
    # Fall back to DuckDuckGo (free)
    try:
        print(f"🔍 Using DuckDuckGo (free) search for: {query}")
        return _search_duckduckgo(query, num_results)
    except Exception as e:
        print(f"❌ DuckDuckGo search failed: {e}")
        return []

def search_images(query: str, num_results: int = 6) -> List[Dict[str, Any]]:
    """
    Search for images
    Priority: SerpAPI > DuckDuckGo (free)
    """
    
    # Try SerpAPI first
    serpapi_key = os.getenv('SERPAPI_API_KEY')
    if serpapi_key:
        try:
            return _search_images_serpapi(query, num_results, serpapi_key)
        except Exception as e:
            print(f"SerpAPI image search failed: {e}, falling back...")
    
    # Fall back to DuckDuckGo
    try:
        return _search_images_duckduckgo(query, num_results)
    except Exception as e:
        print(f"DuckDuckGo image search failed: {e}")
        return []

def _search_serper(query: str, num_results: int, api_key: str) -> List[Dict[str, Any]]:
    """Search using Serper API (Google Search)"""
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    data = {
        'q': query,
        'num': num_results
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    organic = results.get('organic', [])
    
    return [
        {
            'title': result.get('title', ''),
            'link': result.get('link', ''),
            'snippet': result.get('snippet', ''),
            'source': 'serper'
        }
        for result in organic[:num_results]
    ]

def _search_serpapi(query: str, num_results: int, api_key: str) -> List[Dict[str, Any]]:
    """Search using SerpAPI (Google Search)"""
    params = {
        'q': query,
        'engine': 'google',
        'api_key': api_key,
        'num': num_results
    }
    
    url = "https://serpapi.com/search.json?" + urlencode(params)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    organic = results.get('organic_results', [])
    
    return [
        {
            'title': result.get('title', ''),
            'link': result.get('link', ''),
            'snippet': result.get('snippet', ''),
            'source': 'serpapi'
        }
        for result in organic[:num_results]
    ]

def _search_duckduckgo(query: str, num_results: int) -> List[Dict[str, Any]]:
    """Search using DuckDuckGo (free)"""
    try:
        # Try newer package first
        from ddgs import DDGS
    except ImportError:
        try:
            # Fallback to older package name
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("Please install: pip install ddgs")
    
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=num_results))
    
    return [
        {
            'title': result.get('title', ''),
            'link': result.get('href', ''),
            'snippet': result.get('body', ''),
            'source': 'duckduckgo'
        }
        for result in results[:num_results]
    ]

def _search_images_serpapi(query: str, num_results: int, api_key: str) -> List[Dict[str, Any]]:
    """Search images using SerpAPI"""
    params = {
        'q': query,
        'engine': 'google_images',
        'api_key': api_key
    }
    
    url = "https://serpapi.com/search.json?" + urlencode(params)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    images = results.get('images_results', [])
    
    return [
        {
            'title': img.get('title', ''),
            'image_url': img.get('original', ''),
            'thumbnail': img.get('thumbnail', ''),
            'source_url': img.get('link', ''),
            'source': 'serpapi'
        }
        for img in images[:num_results]
    ]

def _search_images_duckduckgo(query: str, num_results: int) -> List[Dict[str, Any]]:
    """Search images using DuckDuckGo (free)"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        try:
            from ddgs import DDGS
        except ImportError:
            raise ImportError("Please install: pip install duckduckgo-search")
    
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=num_results))
    
    return [
        {
            'title': result.get('title', ''),
            'image_url': result.get('image', ''),
            'thumbnail': result.get('thumbnail', ''),
            'source_url': result.get('url', ''),
            'source': 'duckduckgo'
        }
        for result in results[:num_results]
    ]

def _search_exa(query: str, num_results: int, api_key: str) -> List[Dict[str, Any]]:
    """Search using Exa.ai (high-quality AI-focused search)"""
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    data = {
        'query': query,
        'numResults': num_results,
        'type': 'neural',  # Use neural search for better AI/research results
        'contents': {
            'text': True,
            'highlights': True
        }
    }
    
    url = "https://api.exa.ai/search"
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    
    search_results = []
    for result in results.get('results', [])[:num_results]:
        # Extract highlights or use text content
        content = ""
        if result.get('highlights'):
            content = " ".join(result['highlights'][:3])  # First 3 highlights
        elif result.get('text'):
            content = result['text'][:300] + "..." if len(result['text']) > 300 else result['text']
        
        search_results.append({
            'title': result.get('title', ''),
            'link': result.get('url', ''),
            'snippet': content,
            'source': 'exa.ai',
            'score': result.get('score', 0),
            'published_date': result.get('publishedDate', '')
        })
    
    return search_results

def _search_tavily(query: str, num_results: int, api_key: str) -> List[Dict[str, Any]]:
    """Search using Tavily AI (has free tier)"""
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        'api_key': api_key,
        'query': query,
        'search_depth': 'basic',  # Use 'advanced' for deeper search with more tokens
        'max_results': num_results,
        'include_answer': False,  # We'll synthesize our own answer
        'include_raw_content': True
    }
    
    url = "https://api.tavily.com/search"
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    results = response.json()
    
    search_results = []
    for result in results.get('results', [])[:num_results]:
        search_results.append({
            'title': result.get('title', ''),
            'link': result.get('url', ''),
            'snippet': result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', ''),
            'source': 'tavily',
            'score': result.get('score', 0),
            'published_date': result.get('published_date', '')
        })
    
    return search_results

# Test functions
if __name__ == "__main__":
    print("Testing web search...")
    results = search_web("WebWatcher deep research agent", 3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")
        print(f"   Source: {result['source']}")
        print()
    
    print("Testing image search...")
    images = search_images("research agent AI", 2)
    for i, img in enumerate(images, 1):
        print(f"{i}. {img['title']}")
        print(f"   Image: {img['image_url']}")
        print(f"   Source: {img['source']}")
        print()