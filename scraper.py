import requests
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ---------- Helper to find fields ----------
def find_field_after_label(soup, label):
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

# ---------- Get slugs from hamburger menu ----------
def get_game_slugs_from_menu():
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
    return list(dict.fromkeys(slugs))[:20]   # get up to 20

# ---------- Get slugs from WordPress tags API ----------
def get_game_slugs_from_tags(min_count=3, max_pages=3):
    """
    Fetch tags from WordPress REST API, filter by minimum post count,
    return a list of slugs. We lower min_count to get more candidates.
    """
    slugs = []
    for page in range(1, max_pages + 1):
        url = f"https://www.destructoid.com/wp-json/wp/v2/tags?per_page=100&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for tag in data:
                if tag['count'] >= min_count:
                    slugs.append(tag['slug'])
        except Exception as e:
            print(f"Tags API error: {e}")
            break
        time.sleep(0.5)
    return list(dict.fromkeys(slugs))[:30]   # return up to 30

# ---------- Scrape a single game hub ----------
def scrape_game_hub(slug):
    url = f"https://www.destructoid.com/game-hub/{slug}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except:
        return None
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, 'lxml')
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Not Available"
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
    else:
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            p = content_div.find('p')
            if p:
                features = p.get_text(strip=True)[:200] + "..."
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
