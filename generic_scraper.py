import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def _stringify(value):
    """Convert any value to a clean string; join lists, extract from dict, etc."""
    if value is None:
        return "Not Available"
    if isinstance(value, str):
        return value.strip() or "Not Available"
    if isinstance(value, (list, tuple)):
        # Join list items, filtering out empty/None
        items = [str(v).strip() for v in value if v and str(v).strip()]
        return ', '.join(items) if items else "Not Available"
    if isinstance(value, dict):
        # Try common keys
        for key in ['name', 'text', 'value']:
            if key in value and value[key]:
                return str(value[key]).strip()
        # Fallback: return first non‑empty string value
        for k, v in value.items():
            if v and isinstance(v, str):
                return v.strip()
        return "Not Available"
    # Convert other types to string
    s = str(value).strip()
    return s if s else "Not Available"

def extract_json_ld(soup):
    """Extract structured data from JSON-LD script tags."""
    data = {}
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            json_data = json.loads(script.string)
            if isinstance(json_data, list):
                for item in json_data:
                    if item.get('@type') in ['VideoGame', 'Game', 'Product']:
                        data.update(item)
            elif isinstance(json_data, dict):
                if json_data.get('@type') in ['VideoGame', 'Game', 'Product']:
                    data.update(json_data)
        except:
            continue
    return data

def scrape_generic_game(url):
    """Improved generic game page scraper with stringified outputs."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return create_placeholder_game(url)

        soup = BeautifulSoup(resp.text, 'lxml')
        json_ld = extract_json_ld(soup)

        # --- Title ---
        title = None
        if json_ld.get('name'):
            title = _stringify(json_ld['name'])
        if not title:
            meta = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'twitter:title'})
            if meta and meta.get('content'):
                title = _stringify(meta['content'])
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = _stringify(h1.get_text())
        if not title:
            title = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            title = _stringify(title)

        # --- Release Date ---
        release_date = "Not Available"
        date_elem = (soup.find('span', class_='release_date') or
                     soup.find('li', class_='release_date') or
                     soup.find('div', class_='release_date'))
        if date_elem:
            release_date = _stringify(date_elem.get_text())
        if release_date == "Not Available" and json_ld.get('datePublished'):
            release_date = _stringify(json_ld['datePublished'])
        if release_date == "Not Available":
            patterns = [r'release date:?\s*(.+)', r'released:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        release_date = _stringify(m.group(1))
                        break

        # --- Features / Description ---
        features = "Not Available"
        if json_ld.get('description'):
            desc = _stringify(json_ld['description'])
            features = desc[:200] + "..." if len(desc) > 200 else desc
        if features == "Not Available":
            meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta and meta.get('content'):
                desc = _stringify(meta['content'])
                features = desc[:200] + "..." if len(desc) > 200 else desc
        if features == "Not Available":
            summary = soup.find('div', class_='summary') or soup.find('div', class_='product_summary')
            if summary:
                p = summary.find('p')
                if p:
                    text = _stringify(p.get_text())
                    features = text[:200] + "..." if len(text) > 200 else text

        # --- Platforms ---
        platforms = "Not Available"
        platform_elem = (soup.find('span', class_='platform') or
                         soup.find('li', class_='platform') or
                         soup.find('div', class_='platform'))
        if platform_elem:
            platforms = _stringify(platform_elem.get_text())
        if platforms == "Not Available" and json_ld.get('gamePlatform'):
            platforms = _stringify(json_ld['gamePlatform'])
        if platforms == "Not Available":
            keywords = ['PC', 'PlayStation', 'PS5', 'PS4', 'Xbox', 'Nintendo Switch', 'iOS', 'Android']
            found = []
            for kw in keywords:
                if soup.find(string=re.compile(kw, re.I)):
                    found.append(kw)
            if found:
                platforms = ', '.join(set(found))

        # --- Developer ---
        developer = "Not Available"
        dev_elem = (soup.find('span', class_='developer') or
                    soup.find('li', class_='developer') or
                    soup.find('div', class_='developer'))
        if dev_elem:
            developer = _stringify(dev_elem.get_text())
        if developer == "Not Available" and json_ld.get('author'):
            developer = _stringify(json_ld['author'])
        if developer == "Not Available":
            patterns = [r'developer:?\s*(.+)', r'developed by:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        developer = _stringify(m.group(1))
                        break

        # --- Publisher ---
        publisher = "Not Available"
        pub_elem = (soup.find('span', class_='publisher') or
                    soup.find('li', class_='publisher') or
                    soup.find('div', class_='publisher'))
        if pub_elem:
            publisher = _stringify(pub_elem.get_text())
        if publisher == "Not Available" and json_ld.get('publisher'):
            publisher = _stringify(json_ld['publisher'])
        if publisher == "Not Available":
            patterns = [r'publisher:?\s*(.+)', r'published by:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        publisher = _stringify(m.group(1))
                        break

        return {
            'title': title,
            'release_date': release_date,
            'key_features': features,
            'platforms': platforms,
            'developer': developer,
            'publisher': publisher,
            'url': url
        }
    except Exception as e:
        print(f"Generic scrape error on {url}: {e}")
        return create_placeholder_game(url)

def extract_game_links_from_listing(url):
    """
    Given a listing page URL (e.g., Metacritic /game/), return a list of absolute URLs
    pointing to individual game pages.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'lxml')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/game/') and len(href) > 6:
                full_url = 'https://www.metacritic.com' + href
                links.add(full_url)
            # Add other site patterns as needed
        return list(links)
    except Exception as e:
        print(f"Error extracting game links from {url}: {e}")
        return []

def create_placeholder_game(url):
    return {
        'title': url.split('/')[-2] if url.endswith('/') else url.split('/')[-1],
        'release_date': "Not Available",
        'key_features': "Not Available",
        'platforms': "Not Available",
        'developer': "Not Available",
        'publisher': "Not Available",
        'url': url
    }