from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path so we can import scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper

app = Flask(__name__)
CORS(app)  # Allow requests from your GitHub Pages domain

@app.route('/api/scrape', methods=['GET'])
def scrape_games():
    try:
        slugs = scraper.get_game_slugs_from_menu()
        games = []
        for slug in slugs:
            game_data = scraper.scrape_game_hub(slug)
            if game_data:                     # only include successfully scraped pages
                games.append(game_data)
            if len(games) >= 10:
                break
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# For local development
if __name__ == '__main__':
    app.run(debug=True)