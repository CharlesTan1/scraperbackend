from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper

app = Flask(__name__)
CORS(app)

@app.route('/api/scrape', methods=['GET'])
def scrape_destructoid_menu():
    """Return 10 games from Destructoid's menu (missing fields = Not Available)."""
    try:
        slugs = scraper.get_game_slugs_from_menu()
        games = []
        for slug in slugs:
            game_data = scraper.scrape_game_hub(slug)
            games.append(game_data)
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)