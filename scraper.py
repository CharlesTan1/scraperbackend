import requests
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_game_slugs_from_homepage():
    return get_game_slugs_from_given_url("https://www.destructoid.com")

def get_game_slugs_from_given_url(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, 'lxml')
    menu_ul = soup.find('ul', id='destructoid-2025-games-nav')
    if not menu_ul:
        menu_ul = soup.select_one('#off-canvas-nav-grid .menu-section:first-child ul')
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
    return list(dict.fromkeys(slugs))[:15]

def find_field_after_label(soup, label):
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
                next_sib = parent.find_next_sibling(string=True)
                if next_sib and next_sib.strip():
                    return next_sib.strip()
                next_elem = parent.find_next_sibling()
                if next_elem:
                    return next_elem.get_text(strip=True)
    return "Not Available"

def scrape_game_hub(slug):
    url = f"https://www.destructoid.com/game-hub/{slug}/"
    default_result = {
        'title': slug.replace('-', ' ').title(),
        'release_date': "Not Available",
        'description': "Not Available",
        'platforms': "Not Available",
        'developer': "Not Available",
        'publisher': "Not Available",
        'url': url
    }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except:
        return default_result

    if resp.status_code != 200:
        return default_result

    soup = BeautifulSoup(resp.text, 'lxml')

    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else default_result['title']

    release_date = find_field_after_label(soup, "Release Date")
    if release_date == "Not Available":
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            release_date = time_tag['datetime']

    # Description – look for the game-summary paragraph first
    description = "Not Available"
    summary_elem = soup.find('p', class_='game-summary')
    if summary_elem:
        desc = summary_elem.get_text(strip=True)
        description = desc[:200] + "..." if len(desc) > 200 else desc
    else:
        # Fallback to meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc['content']
            description = desc[:200] + "..." if len(desc) > 200 else desc
        else:
            # Fallback to first paragraph in content area
            content = soup.find('div', class_='entry-content') or soup.find('article')
            if content:
                p = content.find('p')
                if p:
                    text = p.get_text(strip=True)
                    description = text[:200] + "..." if len(text) > 200 else text

    platforms = find_field_after_label(soup, "Platforms")
    if platforms == "Not Available":
        platform_links = soup.find_all('a', href=re.compile(r'/tag/(pc|ps5|xbox|switch|nintendo|playstation)'))
        if platform_links:
            platforms = ', '.join(set(link.get_text(strip=True) for link in platform_links))

    developer = find_field_after_label(soup, "Developer")
    publisher = find_field_after_label(soup, "Publisher")

    time.sleep(1)

    return {
        'title': title,
        'release_date': release_date,
        'description': description,
        'platforms': platforms,
        'developer': developer,
        'publisher': publisher,
        'url': url
    }