import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def scrape_generic_game(url):
    """
    Universal scraper that attempts to extract game information from any URL.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return create_placeholder_game(url)

        soup = BeautifulSoup(resp.text, 'lxml')

        title = extract_title(soup, url)
        release_date = extract_release_date(soup)
        features = extract_description(soup)
        platforms = extract_platforms(soup)
        developer = extract_developer(soup)
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
    meta = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'twitter:title'})
    if meta and meta.get('content'):
        return meta['content'].strip()
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]

def extract_release_date(soup):
    patterns = [
        (r'release date:?\s*(.+)', re.I),
        (r'released:?\s*(.+)', re.I),
        (r'out now:?\s*(.+)', re.I),
    ]
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        return time_tag['datetime']
    return "Not Available"

def extract_description(soup):
    meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
    if meta and meta.get('content'):
        desc = meta['content']
        return desc[:200] + "..." if len(desc) > 200 else desc
    article = soup.find('article') or soup.find('main')
    if article:
        p = article.find('p')
        if p:
            text = p.get_text(strip=True)
            return text[:200] + "..." if len(text) > 200 else text
    return "Not Available"

def extract_platforms(soup):
    platform_keywords = ['PC', 'PlayStation', 'PS5', 'PS4', 'Xbox', 'Nintendo Switch', 'iOS', 'Android']
    found = []
    for platform in platform_keywords:
        if soup.find(string=re.compile(platform, re.I)) or soup.find('a', href=re.compile(platform.lower(), re.I)):
            found.append(platform)
    return ', '.join(set(found)) if found else "Not Available"

def extract_developer(soup):
    patterns = [(r'developer:?\s*(.+)', re.I), (r'developed by:?\s*(.+)', re.I)]
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    return "Not Available"

def extract_publisher(soup):
    patterns = [(r'publisher:?\s*(.+)', re.I), (r'published by:?\s*(.+)', re.I)]
    for pattern, flags in patterns:
        for element in soup.find_all(string=re.compile(pattern, flags)):
            match = re.search(pattern, element, flags)
            if match:
                return match.group(1).strip()
    return "Not Available"

def create_placeholder_game(url):
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
