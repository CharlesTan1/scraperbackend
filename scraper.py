import requests
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_game_slugs_from_menu():
    """Extract the 10 game slugs directly from the homepage menu."""
    url = "https://www.destructoid.com"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'lxml')
    menu_ul = soup.find('ul', id='destructoid-2025-games-nav')
    if not menu_ul:
        # Fallback selector
        menu_ul = soup.select_one('#off-canvas-nav-grid .menu-section:first-child ul')
    if not menu_ul:
        return []
    slugs = []
    for a in menu_ul.find_all('a', href=True):
        href = a['href']
        # Ignore the "All Guides" link
        if '/category/guides' in href:
            continue
        if '/tag/' in href:
            slug = href.split('/tag/')[-1].strip('/')
            slugs.append(slug)
    # Return exactly the 10 slugs (in case of duplicates, but there shouldn't be)
    return slugs[:10]

def find_field_after_label(soup, label):
    """Helper to find text after a label (case‑insensitive)."""
    elem = soup.find(string=re.compile(r'^\s*' + re.escape(label) + r'\s*$', re.IGNORECASE))
    if not elem:
        elem = soup.find(string=re.compile(re.escape(label), re.IGNORECASE))
    if elem:
        parent = elem.find_parent()
        if parent:
            next_sib = parent.find_next_sibling(string=True)
            if next_sib and next_sib.strip():
                return next_sib.strip()
            next_elem = parent.find_next_sibling()
            if next_elem:
                return next_elem.get_text(strip=True)
    return "Not Available"

def scrape_game_hub(slug):
    """
    Try to fetch the game hub page. If it exists and contains fields, use them.
    Otherwise return a minimal entry with just the title.
    """
    url = f"https://www.destructoid.com/game-hub/{slug}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except:
        # If request fails, still return a placeholder
        return {
            'title': slug.replace('-', ' ').title(),
            'release_date': "Not Available",
            'key_features': "Not Available",
            'platforms': "Not Available",
            'developer': "Not Available",
            'publisher': "Not Available",
            'url': url
        }
    if resp.status_code != 200:
        # Page not found – still return placeholder with title
        return {
            'title': slug.replace('-', ' ').title(),
            'release_date': "Not Available",
            'key_features': "Not Available",
            'platforms': "Not Available",
            'developer': "Not Available",
            'publisher': "Not Available",
            'url': url
        }

    soup = BeautifulSoup(resp.text, 'lxml')

    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else slug.replace('-', ' ').title()

    # Release Date
    release_date = find_field_after_label(soup, "RELEASE DATE")
    if release_date == "Not Available":
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            release_date = time_tag['datetime']

    # Features
    features = "Not Available"
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        features = desc[:200] + "..." if len(desc) > 200 else desc

    # Platforms
    platforms = find_field_after_label(soup, "PLATFORMS")
    if platforms == "Not Available":
        platform_links = soup.find_all('a', href=re.compile(r'/tag/(pc|ps5|xbox|switch|nintendo|playstation)'))
        if platform_links:
            platforms = ', '.join(set(link.get_text(strip=True) for link in platform_links))

    # Developer
    developer = find_field_after_label(soup, "DEVELOPER")
    # Publisher
    publisher = find_field_after_label(soup, "PUBLISHER")

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
