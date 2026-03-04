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
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'lxml')

    menu_ul = soup.find('ul', id='destructoid-2025-games-nav')
    if not menu_ul:
        menu_ul = soup.select_one('#off-canvas-nav-grid .menu-section:first-child ul')
    if not menu_ul:
        return []

    slugs = []
    for a in menu_ul.find_all('a', href=True):
        href = a['href']
        if '/tag/' in href:
            slug = href.split('/tag/')[-1].strip('/')
            slugs.append(slug)
    return list(dict.fromkeys(slugs))[:15]

def find_field_after_label(soup, label):
    """
    Look for an element containing the label text (case-insensitive, exact match preferred),
    then return the text of the next sibling or the next element.
    """
    # Try exact match first (case-insensitive)
    elem = soup.find(string=re.compile(r'^\s*' + re.escape(label) + r'\s*$', re.IGNORECASE))
    if not elem:
        # Try partial match (label appears as part of text)
        elem = soup.find(string=re.compile(re.escape(label), re.IGNORECASE))
    if elem:
        # Get the parent and then the next sibling that contains text
        parent = elem.find_parent()
        if parent:
            # Look for the next sibling with text
            next_sib = parent.find_next_sibling(string=True)
            if next_sib and next_sib.strip():
                return next_sib.strip()
            # Otherwise, look for the next element with text
            next_elem = parent.find_next_sibling()
            if next_elem:
                return next_elem.get_text(strip=True)
    return "Not Available"

def scrape_game_hub(slug):
    """
    Scrape a single game hub page (https://www.destructoid.com/game-hub/{slug}/)
    and return a dict with the required fields.
    """
    url = f"https://www.destructoid.com/game-hub/{slug}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except:
        return None
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, 'lxml')

    # 1. Game Title (usually in <h1>)
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Not Available"

    # 2. Release Date – try common labels
    release_date = find_field_after_label(soup, "RELEASE DATE")
    if release_date == "Not Available":
        # Fallback: look for <time> element
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            release_date = time_tag['datetime']
        else:
            release_date = "Not Available"

    # 3. Key Features – use meta description or first paragraph
    features = "Not Available"
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        features = desc[:200] + "..." if len(desc) > 200 else desc
    else:
        # Try the first paragraph after the title
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            p = content_div.find('p')
            if p:
                features = p.get_text(strip=True)[:200] + "..."

    # 4. Platforms – look for "PLATFORMS" label (may be absent)
    platforms = find_field_after_label(soup, "PLATFORMS")
    if platforms == "Not Available":
        # Alternative: look for platform tags
        platform_links = soup.find_all('a', href=re.compile(r'/tag/(pc|ps5|xbox|switch|nintendo|playstation)'))
        if platform_links:
            platforms = ', '.join(set(link.get_text(strip=True) for link in platform_links))

    # 5. Developer
    developer = find_field_after_label(soup, "DEVELOPER")

    # 6. Publisher
    publisher = find_field_after_label(soup, "PUBLISHER")

    # Polite delay between requests
    time.sleep(1)

    return {
        'title': title,
        'release_date': release_date,
        'key_features': features,
        'platforms': platforms,
        'developer': developer,
        'publisher': publisher,
        'url': url
    }
