import wikipediaapi
import re

USER_AGENT = 'DestructoidGameScraper/1.0 (educational project)'
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent=USER_AGENT
)

def _extract_infobox_value(page, field_name):
    text = page.text[:2000]
    patterns = [
        r'\|?\s*' + field_name + r'\s*=\s*(.+?)(?:\n|\|)',
        r'\|?\s*' + field_name.lower() + r'\s*=\s*(.+?)(?:\n|\|)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            value = re.sub(r'\[\[|\]\]|\{\{|\}\}', '', value)
            value = re.sub(r'<[^>]+>', '', value)
            return value if value and value != "''" else None
    return None

def scrape_from_wikipedia(game_title):
    try:
        search = game_title.replace('-', ' ').title()
        # Handle special cases
        if "Baldurs Gate 3" in search:
            search = "Baldur's Gate III"
        elif "Grand Theft Auto 6" in search or "GTA 6" in search:
            search = "Grand Theft Auto VI"

        page = wiki_wiki.page(search)
        if not page.exists():
            alt = search.replace("'s", "s")
            if alt != search:
                page = wiki_wiki.page(alt)
        if not page.exists():
            return None

        developer = _extract_infobox_value(page, 'developer')
        publisher = _extract_infobox_value(page, 'publisher')
        release_date = _extract_infobox_value(page, 'released')
        platforms = _extract_infobox_value(page, 'platforms')

        summary = page.summary.split('\n')[0] if page.summary else None
        features = summary[:200] + "..." if summary and len(summary) > 200 else summary
        if not features:
            genre = _extract_infobox_value(page, 'genre')
            features = genre[:200] + "..." if genre else None

        return {
            'title': page.title,
            'release_date': release_date or "Not Available",
            'key_features': features or "Not Available",
            'platforms': platforms or "Not Available",
            'developer': developer or "Not Available",
            'publisher': publisher or "Not Available",
            'wikipedia_url': page.fullurl
        }
    except Exception as e:
        print(f"Wikipedia scrape error: {e}")
        return None