import requests
from bs4 import BeautifulSoup
import time

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

    # Locate the games menu <ul> – using the exact id you provided
    menu_ul = soup.find('ul', id='destructoid-2025-games-nav')
    if not menu_ul:
        # Fallback: broader selector inside the off-canvas grid
        menu_ul = soup.select_one('#off-canvas-nav-grid .menu-section:first-child ul')
    if not menu_ul:
        return []

    slugs = []
    for a in menu_ul.find_all('a', href=True):
        href = a['href']
        # Links look like "/tag/game-name/" or sometimes absolute
        if '/tag/' in href:
            slug = href.split('/tag/')[-1].strip('/')
            slugs.append(slug)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(slugs))[:15]   # get up to 15 slugs

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

    # --- Helper to find text after a label ---
    def find_field(label):
        elem = soup.find(string=label)
        if elem and elem.find_next():
            return elem.find_next().get_text(strip=True)
        return "Not Available"

    # 1. Game Title (usually in <h1>)
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Not Available"

    # 2. Release Date – try <time> element first, then "Release Date:" label
    release_date = "Not Available"
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        release_date = time_tag['datetime']
    else:
        release_date = find_field("Release Date")

    # 3. Key Features – use meta description as a fallback
    features = "Not Available"
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
        features = desc[:200] + "..." if len(desc) > 200 else desc

    # 4. Platforms – look for "Platforms:" label
    platforms = find_field("Platforms:")

    # 5. Developer
    developer = find_field("Developer:")

    # 6. Publisher
    publisher = find_field("Publisher:")

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
