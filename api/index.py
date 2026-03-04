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
        # Get slugs from both sources
        menu_slugs = scraper.get_game_slugs_from_menu()
        tags_slugs = scraper.get_game_slugs_from_tags()
        # Combine and deduplicate
        all_slugs = list(dict.fromkeys(menu_slugs + tags_slugs))
        print(f"Total candidate slugs: {len(all_slugs)}")  # visible in Vercel logs

        games = []
        for slug in all_slugs:
            game_data = scraper.scrape_game_hub(slug)
            if game_data:
                games.append(game_data)
                print(f"Added {slug}, total now {len(games)}")
            else:
                print(f"Skipped {slug} (no hub)")
            if len(games) >= 10:
                break

        return jsonify(games)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
