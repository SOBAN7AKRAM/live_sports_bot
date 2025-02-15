from celery import shared_task
import redis
import requests
import json 
import time
from datetime import datetime, timedelta
from fractions import Fraction
from .models import User
import dotenv
import os

# Load environment variables
dotenv.load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# connect to redis
r = redis.Redis(host='localhost', port=6379, db=0)

BASE_URL = "https://www.sofascore.com/api/v1"

@shared_task
def fetch_and_process_matches():
    """
    Task to fetch and process matches.
    Task will run every minute.
    """
    print("started")
    matches = fetch_matches("basketball")
    print("matches fetched")
    process_favourites(matches)
    print("matches processed")
    


def fetch_matches(sport_id):
    """
    Fetch today matches for a given sport.
    Extract necessary details of events from the response.
    Return the list of dictionaries with match details.
    """

    # Getting the current date
    today = datetime.now().strftime("%Y-%m-%d")
    response = requests.get(f"https://www.sofascore.com/api/v1/sport/{sport_id}/scheduled-events/{today}")
    data = response.json()
    events = data.get("events")
    
    # List to store matches
    matches = []
    
    # loop to extract necessary match details
    for event in events:
        
        # Dictionary to store match details
        match = {}
        match["sports_id"] = sport_id,
        match["event_id"] = event.get("id")
        match["tournament_name"] = event.get("tournament").get("name")
        match["category_name"] = event.get("tournament").get("category").get("name")
        match["status"] = event.get("status").get("description")
        match["home_team_name"] = event.get("homeTeam").get("name")
        match["home_team_id"] = event.get("homeTeam").get("id")
        match["home_score"] = event.get("homeScore")
        match["away_team_name"] = event.get("awayTeam").get("name")
        match["away_team_id"] = event.get("awayTeam").get("id")
        match["away_score"] = event.get("awayScore")
        matches.append(match)

    return matches

def fetch_odds(event_id):
    """
    Fetch odds for a given event.
    Return the list of dictionaries with odds details.
    """
    
    response = requests.get(f"{BASE_URL}//event/{event_id}/odds/1/all")
    data = response.json()
    markets = data.get("markets")
    return markets
        
def process_favourites(matches):
    """
    Insert the favourite team and odds in redis if match has not started yet.
    If the match is at (halftime, firstset, keyevent) of (Basketball, Tennis, Handball) 
    and favourite is losing, generate an alert and delete favourite from redis.
    """
    
    count = 1
    # Loop through matches
    for match in matches:
        event_id = match["event_id"]
        print(f"Processing match {count} with event_id {event_id}")
        count += 1
        # Create a key name for the favourite data
        favourite_key = f"favourite:{event_id}"
        
        # if match is not started and favourite is not present in redis insert favourite
        if not r.exists(favourite_key) and match["status"] == "Not started":
            
            # fetch odds for the event
            markets = fetch_odds(event_id)
            
            if not markets:
                continue
            # Extract odds and calculate favourite
            home_odds_frac = markets[0].get("choices")[0].get("fractionalValue")
            away_odds_frac = markets[0].get("choices")[1].get("fractionalValue")
            if home_odds_frac and away_odds_frac:
                home_odds = 1 + float(Fraction(home_odds_frac))
                away_odds = 1 + float(Fraction(away_odds_frac))
                
                if home_odds < away_odds:
                    favorite = "home"
                else:
                    favorite = "away"
                favourite_data = {
                    "favourite": favorite,    
                    "home_odds": home_odds,    
                    "away_odds": away_odds
                }
                r.set(favourite_key, json.dumps(favourite_data), ex=86400)
           
        # For Basketball if match is at halftime check if favourite is losing and remove from redis
        if match["status"] == "Halftime":
            if r.exists(favourite_key):
                stored_data = json.loads(r.get(favourite_key))
                
                # Check if favourite is losing
                if stored_data["favourite"] == "home":
                    if match["home_score"] < match["away_score"]:
                        message = f"Favourite {match['home_team_name']} is losing at halftime."
                        send_alert(match, stored_data, message)
                        
                elif stored_data["favourite"] == "away":
                    if match["away_score"] < match["home_score"]:
                        message = f"Favourite {match['away_team_name']} is losing at halftime."
                        send_alert(match, stored_data)
                        
                # In any case delete favourite from the redis
                r.delete(favourite_key)   
        else:
            if r.exists(favourite_key):
                r.delete(favourite_key)

    
def send_alert(match, stored_data, message):
    """
    Send the alert to telegram to all the valid users.
    """
    
    event_id = match["event_id"]
    
    # Fetch current odds
    markets = fetch_odds(event_id)
    home_odds_frac = markets[0].get("choices")[0].get("fractionalValue")
    away_odds_frac = markets[0].get("choices")[1].get("fractionalValue")
    if home_odds_frac and away_odds_frac:
        home_odds = 1 + float(Fraction(home_odds_frac))
        away_odds = 1 + float(Fraction(away_odds_frac))
    
    # Query all users with a valid access token
    valid_users = User.objects.filter(
        access_token__isnull=False,
        expiration_date__gt=datetime.now()
    )
    
    
    # Format the message
    alert = f"🚨 Alert: {message}\n\n"
    f"🏀 {match['home_team_name']}(Home) vs {match['away_team_name']}(Away)\n"
    f"🏀 {match['sports_id']}\n"
    f"🏆 {match['tournament_name']}\n"
    f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    f"📊 Pre-match odds: {stored_data['home_odds']}(Home) - {stored_data['away_odds']}(Away)\n"
    f"📊 Current odds: {home_odds}(Home) - {away_odds}(Away)\n\n"
    f" Score: {match["home_score"]}(Home) - {match["away_score"]}(Away)\n"
    
    
    # Send alert to valid users only
    for user in valid_users:
        pay_load = {
            "chat_id": user.telegram_id,
            "text": alert
        }
        try:
            response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=pay_load)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to user {user.telegram_id}: {e}")
            continue