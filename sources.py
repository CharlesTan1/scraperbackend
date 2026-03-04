import os
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

class SourceManager:
    def __init__(self):
        self.sources = [
            DestructoidSource(),
            IGDBsource()
        ]
    
    def get_game_data(self, game_name, game_slug=None):
        aggregated = {
            'title': game_name,
            'release_date': "Not Available",
            'key_features': "Not Available",
            'platforms': "Not Available",
            'developer': "Not Available",
            'publisher': "Not Available",
            'sources_used': []
        }
        
        for source in self.sources:
            try:
                data = source.fetch(game_name, game_slug)
                if not data:
                    continue
                for field in ['release_date', 'key_features', 'platforms', 'developer', 'publisher']:
                    if aggregated[field] == "Not Available" and data.get(field) and data[field] != "Not Available":
                        aggregated[field] = data[field]
                        aggregated['sources_used'].append({field: source.name})
            except Exception as e:
                print(f"Error with {source.name}: {e}")
            time.sleep(0.5)
        
        return aggregated


class DestructoidSource:
    name = "Destructoid"
    
    def fetch(self, game_name, game_slug=None):
        if not game_slug:
            return None
        from scraper import scrape_game_hub
        return scrape_game_hub(game_slug)


class IGDBsource:
    name = "IGDB"
    
    def __init__(self):
        self.client_id = os.getenv('IGDB_CLIENT_ID')
        self.client_secret = os.getenv('IGDB_CLIENT_SECRET')
        self.token = None
        self.token_expires = 0
        
    def _get_access_token(self):
        if time.time() < self.token_expires:
            return self.token
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        resp = requests.post(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            self.token = data['access_token']
            self.token_expires = time.time() + data['expires_in'] - 60
            return self.token
        else:
            raise Exception(f"Failed to get IGDB token: {resp.text}")
    
    def fetch(self, game_name, game_slug=None):
        if not self.client_id or not self.client_secret:
            print("IGDB credentials missing")
            return None
        
        token = self._get_access_token()
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Build search terms set (comprehensive)
        search_terms = set()
        
        # Original name
        if game_name:
            search_terms.add(game_name)
        
        # Slug with hyphens replaced
        if game_slug:
            search_terms.add(game_slug.replace('-', ' '))
            search_terms.add(game_slug)  # keep hyphenated
        
        # Add apostrophe versions (e.g., "Baldurs" -> "Baldur's")
        for term in list(search_terms):
            words = term.split()
            for i, word in enumerate(words):
                if word.endswith('s') and len(word) > 3 and not word.endswith("'s") and not word.endswith("’s"):
                    candidate = word[:-1] + "'s" + " " + " ".join(words[i+1:])
                    search_terms.add(candidate.strip())
        
        # Convert numbers to Roman numerals and vice versa
        roman_map = {
            '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
            '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X'
        }
        for term in list(search_terms):
            for num, roman in roman_map.items():
                if f" {num}" in term or term.endswith(f" {num}"):
                    search_terms.add(term.replace(f" {num}", f" {roman}"))
                if f" {roman}" in term or term.endswith(f" {roman}"):
                    search_terms.add(term.replace(f" {roman}", f" {num}"))
        
        # Remove punctuation for another variation
        for term in list(search_terms):
            no_punct = re.sub(r"[^\w\s]", "", term)
            if no_punct != term:
                search_terms.add(no_punct)
        
        # Log terms (will appear in Vercel logs)
        print(f"IGDB search terms for {game_name}: {list(search_terms)}")
        
        for term in search_terms:
            print(f"IGDB searching: {term}")
            search_body = f'search "{term}"; fields name,first_release_date,platforms.name,involved_companies.company.name,summary; limit 5;'
            resp = requests.post("https://api.igdb.com/v4/games", headers=headers, data=search_body)
            if resp.status_code != 200:
                continue
            games = resp.json()
            if not games:
                continue
            
            # Take the first result (IGDB returns most relevant first)
            game = games[0]
            print(f"IGDB found: {game.get('name')}")
            
            result = {
                'release_date': "Not Available",
                'key_features': "Not Available",
                'platforms': "Not Available",
                'developer': "Not Available",
                'publisher': "Not Available"
            }
            
            if 'first_release_date' in game:
                ts = game['first_release_date'] / 1000
                result['release_date'] = time.strftime('%Y-%m-%d', time.gmtime(ts))
            
            if 'summary' in game:
                summary = game['summary']
                result['key_features'] = summary[:200] + "..." if len(summary) > 200 else summary
            
            if 'platforms' in game:
                platforms = [p['name'] for p in game['platforms'] if 'name' in p]
                result['platforms'] = ', '.join(platforms[:5])
            
            if 'involved_companies' in game:
                devs = []
                pubs = []
                for ic in game['involved_companies']:
                    if 'company' in ic and 'name' in ic['company']:
                        if ic.get('developer'):
                            devs.append(ic['company']['name'])
                        if ic.get('publisher'):
                            pubs.append(ic['company']['name'])
                if devs:
                    result['developer'] = ', '.join(devs)
                if pubs:
                    result['publisher'] = ', '.join(pubs)
            
            return result
        
        print(f"IGDB no match for {game_name} / {game_slug}")
        return None