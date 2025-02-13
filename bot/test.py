import requests
from dotenv import load_dotenv
import os
import json


def get_favourite_team_by_ml(away_ml_odds: int, home_ml_odds: int) -> str:
    """Get the favourite team based on Moneyline odds"""
    
    
    if not away_ml_odds or not home_ml_odds:
        return None
    if away_ml_odds > 0 and home_ml_odds > 0:
        # Both teams are underdogs, the one with higher positive odds is the underdog
        favorite = "home" if home_ml_odds < away_ml_odds else "away"
    elif away_ml_odds < 0 and home_ml_odds < 0:
        # Both teams are favorites, the one with less negative odds is the favorite
        favorite = "home" if home_ml_odds > away_ml_odds else "away"
    elif away_ml_odds > 0:
        # Away team is an underdog, so home team is the favorite
        favorite = "home"
    else:
        # Home team is an underdog, so away team is the favorite
        favorite = "away"
        
    return favorite

load_dotenv()
API_KEY = os.getenv("SPORT_GAMES_ODDS_API")

url = "https://api.sportsgameodds.com/v1/events"
params = {
    "/": "",
    "sportID": "BASKETBALL",
    "leagueID": "NBA",
    "oddsAvailable": "true",
    "startsBefore": "2025-02-08",
    "includeOpposingOddIDs": "true",
}

headers = {
    "X-Api-Key": API_KEY
}

response = requests.get(url, params=params, headers=headers)

data = json.loads(response.text)
data = data.get("data")

matches = []
for index, event in enumerate(data):
    match = {}
    home, away = event.get("teams").get("home").get("names").get("long"), event.get("teams").get("away").get("names").get("long")
    status = event.get("status").get("started")
    match["home"] = home
    match["away"] = away
    match["status"] = "live" if status else "pre-match"
    away_ml_odds = event.get("odds").get("points-away-game-ml-away").get("odds")
    home_ml_odds = event.get("odds").get("points-home-game-ml-home").get("odds")
    match["favorite"] = get_favourite_team_by_ml(int(away_ml_odds), int(home_ml_odds))
    match["away_ml_odds"] = int(away_ml_odds)
    match["home_ml_odds"] = int(home_ml_odds)
    matches.append(match)
