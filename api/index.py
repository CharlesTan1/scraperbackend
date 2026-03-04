from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import re
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper
import generic_scraper
from sources import SourceManager

app = Flask(__name__)
CORS(app)

source_manager = SourceManager()

@app.route('/api/scrape', methods=['GET'])
def scrape_destructoid_menu():
    """Get 10 games from Destructoid menu, enriched with IGDB data."""
    try:
        slugs = scraper.get_game_slugs_from_menu()
        games = []
        for slug in slugs:
            game_name = slug.replace('-', ' ').title()
            game_data = source_manager.get_game_data(game_name, slug)
            games.append(game_data)
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    """Scrape any game URL using multi‑source fusion."""
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        game_info = extract_game_info_from_url(url)
        
        if game_info and game_info.get('name'):
            aggregated = source_manager.get_game_data(
                game_info['name'],
                game_info.get('slug')
            )
            return jsonify([aggregated])
        else:
            game_data = generic_scraper.scrape_generic_game(url)
            return jsonify([game_data])
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

def detect_source(url):
    domain = urlparse(url).netloc.lower()
    if 'destructoid.com' in domain:
        return 'destructoid'
    return 'unknown'

def extract_game_info_from_url(url):
    source = detect_source(url)
    if source == 'destructoid':
        slug = extract_destructoid_slug(url)
        if slug:
            return {
                'name': slug.replace('-', ' ').title(),
                'slug': slug
            }
    path = urlparse(url).path.strip('/')
    if path:
        last_part = path.split('/')[-1]
        name = last_part.replace('-', ' ').replace('_', ' ').title()
        return {'name': name, 'slug': None}
    return None

def extract_destructoid_slug(url):
    match = re.search(r'/(?:game-hub|tag)/([^/]+)/?', url)
    return match.group(1) if match else None

if __name__ == '__main__':
    app.run(debug=True)