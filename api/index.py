from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scraper

app = Flask(__name__)
CORS(app)

@app.route('/api/scrape', methods=['GET'])
def scrape_homepage_menu():
    try:
        slugs = scraper.get_game_slugs_from_homepage()
        games = []
        for slug in slugs:
            game_data = scraper.scrape_game_hub(slug)
            games.append(game_data)
        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape-from-url', methods=['POST'])
def scrape_from_url():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        slugs = scraper.get_game_slugs_from_given_url(url)
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