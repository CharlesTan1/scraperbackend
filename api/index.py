from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper

app = Flask(__name__)
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/scrape')
def scrape_games():
    try:
        slugs = scraper.get_game_slugs_from_menu()
        games = []
        for slug in slugs:
            game_data = scraper.scrape_game_hub(slug)
            games.append(game_data)
            # We already have exactly 10 slugs, so no need to break early
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
