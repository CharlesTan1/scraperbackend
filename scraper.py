import requests
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_game_slugs_from_menu():
    """
    Fetch destructoid.com main page, extract game slugs from the static menu.
    Returns a list of unique slugs (e.g., 'baldurs-gate-3').
    """
    url = "https://www.destructoid.com"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch homepage: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'lxml')

    # Try multiple possible menu containers
    menu_ul = soup.find('ul', id='destructoid-2025-games-nav')
    if not menu_ul:
        menu_ul = soup.select_one('#off-canvas-nav-grid .menu-section:first-child ul')
    if not menu_ul:
        # If still not found, try a more generic selector
        menu_ul = soup.find('ul', class_='menu-list')
    if not menu_ul:
        return []

    slugs = []
    for a in menu_ul.find_all('a', href=True):
        href = a['href']
        if '/category/guides' in href:
            continue
        if '/tag/' in href:
            slug = href.split('/tag/')[-1].strip('/')
            if slug:
                slugs.append(slug)
    # Remove duplicates and return up to 15 (we'll later limit to 10)
    return list(dict.fromkeys(slugs))[:15]

def find_field_after_label(soup, label):
    """
    Look for an element containing the label text (case-insensitive, with optional colon),
    then return the text of the next element or sibling.
    """
    # Try various patterns: exact label, label with colon, uppercase, etc.
    patterns = [
        r'^\s*' + re.escape(label) + r'\s*:?\s*$',
        r'^\s*' + re.escape(label.upper()) + r'\s*:?\s*$',
        r'^\s*' + re.escape(label.lower()) + r'\s*:?\s*$',
        r'^\s*' + re.escape(label.title()) + r'\s*:?\s*$',
    ]
    for pattern in patterns:
        elem = soup.find(string=re.compile(pattern))
        if elem:
            parent = elem.find_parent()
            if parent:
                # Look for the next sibling that contains text
                next_sib = parent.find_next_sibling(string=True)
                if next_sib and next_sib.strip():
                    return next_sib.strip()
                # Otherwise look for the next element's text
                next_elem = parent.find_next_sibling()
                if next_elem:
                    return next_elem.get_text(strip=True)
    return "Not Available"

def scrape_game_hub(slug):
    """
    Scrape a single game hub page. If the page is missing, return a placeholder
    with the title derived from the slug.
    """
    url = f"https://www.destructoid.com/game-hub/{slug}/"
    # Default placeholder in case of failure
    default_result = {
        'title': slug.replace('-', ' ').title(),
        'release_date': "Not Available",
        'key_features': "Not Available",
        'platforms': "Not Available",
        'developer': "Not Available",
        'publisher': "Not Available",
        'url': url
    }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"Request failed for {slug}: {e}")
        return default_result

    if resp.status_code != 200:
        print(f"Non-200 status for {slug}: {resp.status_code}")
        return default_result

    soup = BeautifulSoup(resp.text, 'lxml')

    # Game Title (usually in <h1>)
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else default_result['title']

    # Release Date
    release_date = find_field_after_label(soup, "Release Date")
    if release_date == "Not Available":
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            release_date = time_tag['datetime']

    # Key Features – try meta description first
    features = "Not Available"
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        features = desc[:200] + "..." if len(desc) > 200 else desc
    else:
        # Fallback: look for a paragraph inside the main content
        content = soup.find('div', class_='entry-content') or soup.find('article')
        if content:
            p = content.find('p')
            if p:
                text = p.get_text(strip=True)
                features = text[:200] + "..." if len(text) > 200 else text

    # Platforms
    platforms = find_field_after_label(soup, "Platforms")
    if platforms == "Not Available":
        # Look for platform tags in links
        platform_links = soup.find_all('a', href=re.compile(r'/tag/(pc|ps5|xbox|switch|nintendo|playstation)'))
        if platform_links:
            platforms = ', '.join(set(link.get_text(strip=True) for link in platform_links))

    # Developer
    developer = find_field_after_label(soup, "Developer")

    # Publisher
    publisher = find_field_after_label(soup, "Publisher")

    time.sleep(1)  # polite delay

    return {
        'title': title,
        'release_date': release_date,
        'key_features': features,
        'platforms': platforms,
        'developer': developer,
        'publisher': publisher,
        'url': url
    }