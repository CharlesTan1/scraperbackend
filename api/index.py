from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import re
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper
import generic_scraper  # We'll create this new module

app = Flask(__name__)
CORS(app)

# Mode 1: Destructoid menu scraping (your existing feature)
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

# Mode 2: Generic URL input - scrape any game page
@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Detect which website this is
        source = detect_source(url)
        
        # Route to appropriate scraper
        if source == 'destructoid':
            # Extract slug from Destructoid URL
            slug = extract_destructoid_slug(url)
            game_data = scraper.scrape_game_hub(slug)
        else:
            # Use generic scraper for unknown sites
            game_data = generic_scraper.scrape_generic_game(url)
        
        return jsonify([game_data])  # Return as array for consistency
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

def detect_source(url):
    """Identify which website the URL belongs to"""
    domain = urlparse(url).netloc.lower()
    
    if 'destructoid.com' in domain:
        return 'destructoid'
    elif 'ign.com' in domain:
        return 'ign'
    elif 'gamespot.com' in domain:
        return 'gamespot'
    elif 'metacritic.com' in domain:
        return 'metacritic'
    else:
        return 'unknown'

def extract_destructoid_slug(url):
    """Extract game slug from Destructoid URL"""
    # Handle both /game-hub/slug/ and /tag/slug/ formats
    match = re.search(r'/(?:game-hub|tag)/([^/]+)/?', url)
    if match:
        return match.group(1)
    return None

if __name__ == '__main__':
    app.run(debug=True)
