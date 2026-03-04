import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def _extract_name(obj):
    """Recursively extract name from JSON-LD objects or lists."""
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, list):
        names = [_extract_name(item) for item in obj]
        names = [n for n in names if n and n != "Not Available"]
        return ', '.join(names) if names else None
    if isinstance(obj, dict):
        if 'name' in obj and obj['name']:
            return str(obj['name']).strip()
        if 'text' in obj and obj['text']:
            return str(obj['text']).strip()
        if '@type' in obj and obj['@type'] == 'Organization' and 'name' in obj:
            return str(obj['name']).strip()
        # Recursively search for a 'name' in any nested object
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                found = _extract_name(v)
                if found:
                    return found
        return None
    return str(obj).strip() if obj else None

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
    """Robust generic game page scraper with Metacritic-specific selectors."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return create_placeholder_game(url)

        soup = BeautifulSoup(resp.text, 'lxml')
        json_ld = extract_json_ld(soup)

        # --- Title (unchanged) ---
        title = None
        if json_ld.get('name'):
            title = _extract_name(json_ld['name'])
        if not title:
            meta = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'twitter:title'})
            if meta and meta.get('content'):
                title = meta['content'].strip()
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        if not title:
            title = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            title = title.replace('-', ' ').title()

        # --- Release Date (unchanged) ---
        release_date = "Not Available"
        # Metacritic specific
        date_li = soup.find('li', class_='release_data')
        if date_li:
            date_span = date_li.find('span', class_='data')
            if date_span:
                release_date = date_span.get_text(strip=True)
            else:
                text = date_li.get_text(strip=True)
                match = re.search(r'release date:?\s*(.+)', text, re.I)
                if match:
                    release_date = match.group(1).strip()
                else:
                    release_date = text
        if release_date == "Not Available" and json_ld.get('datePublished'):
            release_date = _extract_name(json_ld['datePublished'])
        if release_date == "Not Available":
            patterns = [r'release date:?\s*(.+)', r'released:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        release_date = m.group(1).strip()
                        break

        # --- Features (unchanged) ---
        features = "Not Available"
        if json_ld.get('description'):
            desc = _extract_name(json_ld['description'])
            if desc:
                features = desc[:200] + "..." if len(desc) > 200 else desc
        if features == "Not Available":
            meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta and meta.get('content'):
                desc = meta['content'].strip()
                features = desc[:200] + "..." if len(desc) > 200 else desc
        if features == "Not Available":
            summary = soup.find('div', class_='summary') or soup.find('div', class_='product_summary')
            if summary:
                p = summary.find('p')
                if p:
                    text = p.get_text(strip=True)
                    features = text[:200] + "..." if len(text) > 200 else text

        # --- Platforms (unchanged) ---
        platforms = "Not Available"
        platform_div = soup.find('div', class_='product_platform')
        if platform_div:
            platform_spans = platform_div.find_all('span', class_='platform')
            if platform_spans:
                platforms = ', '.join([span.get_text(strip=True) for span in platform_spans])
        if platforms == "Not Available" and json_ld.get('gamePlatform'):
            platforms = _extract_name(json_ld['gamePlatform'])
        if platforms == "Not Available":
            keywords = ['PC', 'PlayStation', 'PS5', 'PS4', 'Xbox', 'Nintendo Switch', 'iOS', 'Android']
            found = []
            for kw in keywords:
                if soup.find(string=re.compile(kw, re.I)):
                    found.append(kw)
            if found:
                platforms = ', '.join(set(found))

        # --- Developer: Metacritic modern classes ---
        developer = "Not Available"
        # Find all grouped sections
        sections = soup.find_all('div', class_='c-product-details__section--grouped')
        for section in sections:
            label = section.find('span', class_='c-product-details__section__label')
            if label and "Developer:" in label.get_text(strip=True):
                value_span = section.find('span', class_='c-product-details__section__value')
                if value_span:
                    developer = value_span.get_text(strip=True)
                    break
        if developer == "Not Available":
            # Fallback: older Metacritic classes
            dev_elem = soup.find('li', class_='developer')
            if dev_elem:
                dev_span = dev_elem.find('span', class_='data')
                if dev_span:
                    developer = dev_span.get_text(strip=True)
                else:
                    text = dev_elem.get_text(strip=True)
                    match = re.search(r'developer:?\s*(.+)', text, re.I)
                    if match:
                        developer = match.group(1).strip()
                    else:
                        developer = text
        if developer == "Not Available" and json_ld.get('author'):
            developer = _extract_name(json_ld['author'])
        if developer == "Not Available":
            patterns = [r'developer:?\s*(.+)', r'developed by:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        developer = m.group(1).strip()
                        break

        # --- Publisher: Metacritic modern classes ---
        publisher = "Not Available"
        for section in sections:
            label = section.find('span', class_='c-product-details__section__label')
            if label and "Publisher:" in label.get_text(strip=True):
                value_span = section.find('span', class_='c-product-details__section__value')
                if value_span:
                    publisher = value_span.get_text(strip=True)
                    break
        if publisher == "Not Available":
            pub_elem = soup.find('li', class_='publisher')
            if pub_elem:
                pub_span = pub_elem.find('span', class_='data')
                if pub_span:
                    publisher = pub_span.get_text(strip=True)
                else:
                    text = pub_elem.get_text(strip=True)
                    match = re.search(r'publisher:?\s*(.+)', text, re.I)
                    if match:
                        publisher = match.group(1).strip()
                    else:
                        publisher = text
        if publisher == "Not Available" and json_ld.get('publisher'):
            publisher = _extract_name(json_ld['publisher'])
        if publisher == "Not Available":
            patterns = [r'publisher:?\s*(.+)', r'published by:?\s*(.+)']
            for pattern in patterns:
                match = soup.find(string=re.compile(pattern, re.I))
                if match:
                    m = re.search(pattern, match, re.I)
                    if m:
                        publisher = m.group(1).strip()
                        break

        # Clean up whitespace
        title = re.sub(r'\s+', ' ', title) if title else "Not Available"
        release_date = re.sub(r'\s+', ' ', release_date) if release_date != "Not Available" else "Not Available"
        features = re.sub(r'\s+', ' ', features) if features != "Not Available" else "Not Available"
        platforms = re.sub(r'\s+', ' ', platforms) if platforms != "Not Available" else "Not Available"
        developer = re.sub(r'\s+', ' ', developer) if developer != "Not Available" else "Not Available"
        publisher = re.sub(r'\s+', ' ', publisher) if publisher != "Not Available" else "Not Available"

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
    """Extract game links from a Metacritic listing page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'lxml')
        links = set()
        # Modern Metacritic listing uses .c-productCard
        for card in soup.select('.c-productCard'):
            link = card.find('a', href=True)
            if link:
                href = link['href']
                if href.startswith('http'):
                    links.add(href)
                else:
                    links.add('https://www.metacritic.com' + href)
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