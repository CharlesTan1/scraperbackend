import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def scrape_generic_game(url):
    """
    Universal scraper that attempts to extract game information from any URL.
    Uses common patterns found across gaming websites.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return create_placeholder_game(url)
        
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # Try to extract title from various sources
        title = extract_title(soup, url)
        
        # Try to find release date
        release_date = extract_release_date(soup)
        
        # Try to find description/features
        features = extract_description(soup)
        
        # Try to find platforms
        platforms = extract_platforms(soup)
        
        # Try to find developer
        developer = extract_developer(soup)
        
        # Try to find publisher
        publisher = extract_publisher(soup)
        
        return {
            'title': title,
            'release_date': release_date,
            'key_features': features,
            'platforms': platforms,
            'developer': developer,
            'publisher': publisher,
            'url': url,
            'source': 'generic'
        }
        
    except Exception as e:
        print(f"Generic scrape error: {e}")
        return create_placeholder_game(url)

def extract_title(soup, url):
    """Extract title from common locations"""
    # Try meta tags first
    meta_title = soup.find('meta', {'property': 'og:title'}) or \
                 soup.find('meta', {'name': 'twitter:title'})
    if meta_title and meta_title.get('content'):
        return meta_title['content'].strip()
    
    # Try h1
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    
    # Try title tag
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    
    # Fallback to URL
    return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]

def extract_release_date(soup):
    """Common patterns for release dates"""
    patterns = [
        (r'release date:?\s*(.+)', re.I),
        (r'released:?\s*(.+)', re.I),
        (r'out now:?\s*(.+)', re.I),
        (r'launch date:?\s*(.+)', re.I)
    ]
    
    # Look for text patterns
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    
    # Try time elements
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime']
    
    # Try schema.org markup
    date_props = soup.find_all(attrs={'itemprop': 'datePublished'})
    if date_props:
        return date_props[0].get('content', date_props[0].get_text(strip=True))
    
    return "Not Available"

def extract_description(soup):
    """Extract description from meta tags or content"""
    # Try meta description
    meta_desc = soup.find('meta', {'name': 'description'}) or \
                soup.find('meta', {'property': 'og:description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        return desc[:200] + "..." if len(desc) > 200 else desc
    
    # Try first paragraph of content
    article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
    if article:
        p = article.find('p')
        if p:
            text = p.get_text(strip=True)
            return text[:200] + "..." if len(text) > 200 else text
    
    return "Not Available"

def extract_platforms(soup):
    """Look for platform information"""
    platform_keywords = ['PC', 'PlayStation', 'PS5', 'PS4', 'Xbox', 
                         'Nintendo Switch', 'iOS', 'Android', 'Mobile']
    
    found = []
    
    # Look in specific platform sections
    platform_section = soup.find(string=re.compile(r'platforms?:', re.I))
    if platform_section:
        parent = platform_section.find_parent()
        if parent:
            text = parent.get_text()
            for platform in platform_keywords:
                if platform.lower() in text.lower():
                    found.append(platform)
    
    # Scan for platform links
    for platform in platform_keywords:
        if soup.find('a', href=re.compile(platform.lower(), re.I)) or \
           soup.find(string=re.compile(platform, re.I)):
            found.append(platform)
    
    return ', '.join(set(found)) if found else "Not Available"

def extract_developer(soup):
    """Find developer information"""
    patterns = [
        (r'developer:?\s*(.+)', re.I),
        (r'developed by:?\s*(.+)', re.I),
        (r'studio:?\s*(.+)', re.I)
    ]
    
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    
    # Try schema.org
    dev = soup.find(attrs={'itemprop': 'author'}) or \
          soup.find(attrs={'itemprop': 'creator'})
    if dev:
        return dev.get_text(strip=True)
    
    return "Not Available"

def extract_publisher(soup):
    """Find publisher information"""
    patterns = [
        (r'publisher:?\s*(.+)', re.I),
        (r'published by:?\s*(.+)', re.I)
    ]
    
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    
    return "Not Available"

def create_placeholder_game(url):
    """Create placeholder when scraping fails"""
    return {
        'title': url.split('/')[-2] if url.endswith('/') else url.split('/')[-1],
        'release_date': "Not Available",
        'key_features': "Not Available",
        'platforms': "Not Available",
        'developer': "Not Available",
        'publisher': "Not Available",
        'url': url,
        'source': 'placeholder'
    }
