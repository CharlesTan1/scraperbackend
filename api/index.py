from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import re
from urllib.parse import urlparse

# Add parent directory to path so we can import scraper modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper
import generic_scraper

app = Flask(__name__)
CORS(app)  # Allow requests from your GitHub Pages domain

# ---------- Destructoid menu scraping (original feature) ----------
@app.route('/api/scrape', methods=['GET'])
def scrape_destructoid_menu():
    try:
        slugs = scraper.get_game_slugs_from_menu()
        games = []
        for slug in slugs:
            game_data = scraper.scrape_game_hub(slug)
            games.append(game_data)
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Generic URL input scraping (new feature) ----------
@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        source = detect_source(url)
        if source == 'destructoid':
            slug = extract_destructoid_slug(url)
            if slug:
                game_data = scraper.scrape_game_hub(slug)
            else:
                game_data = generic_scraper.scrape_generic_game(url)
        else:
            game_data = generic_scraper.scrape_generic_game(url)

        return jsonify([game_data])  # return as array for consistency
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Health check ----------
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

def detect_source(url):
    domain = urlparse(url).netloc.lower()
    if 'destructoid.com' in domain:
        return 'destructoid'
    # Add more sites here as you like
    return 'unknown'

def extract_destructoid_slug(url):
    match = re.search(r'/(?:game-hub|tag)/([^/]+)/?', url)
    return match.group(1) if match else None

if __name__ == '__main__':
    app.run(debug=True)
