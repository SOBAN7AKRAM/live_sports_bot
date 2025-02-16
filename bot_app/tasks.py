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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
dotenv.load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# connect to redis
r = redis.Redis(host='localhost', port=6379, db=0)

BASE_URL = "https://www.sofascore.com/api/v1"

@shared_task
def fetch_and_process_live_basketball():
    """
    Task to fetch and process matches.
    Task will run every minute.
    """
    print("started")
    sport_id = "basketball"
    url = f"https://www.sofascore.com/api/v1/sport/{sport_id}/events/live"
    matches = fetch_matches(url, sport_id)
    print("basketball matches fetched ", len(matches))
    process_favourites(matches)
    print("basketball matches processed")
    
@shared_task
def fetch_and_process_upcoming_basketball():
    """
    Task to fetch upcoming matches before 1 hour of the next day.
    """
    sport_id = "basketball"
    tomorrow = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.sofascore.com/api/v1/sport/{sport_id}/scheduled-events/{tomorrow}"
    matches = fetch_matches(url, sport_id)
    process_favourites(matches)
    
@shared_task
def fetch_and_process_live_tennis():
    """
    Task to fetch and process matches.
    Task will run every minute.
    """
    print("started tennis")
    sport_id = "tennis"
    url = f"https://www.sofascore.com/api/v1/sport/{sport_id}/events/live"
    matches = fetch_matches(url, sport_id)
    print("tennis matches fetched ", len(matches))
    process_favourites(matches)
    print("tennis matches processed")
    
@shared_task
def fetch_and_process_upcoming_tennis():
    """
    Task to fetch upcoming matches before 1 hour of the next day.
    """
    sport_id = "tennis"
    tomorrow = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.sofascore.com/api/v1/sport/{sport_id}/scheduled-events/{tomorrow}"
    matches = fetch_matches(url, sport_id)
    process_favourites(matches)
    
# @shared_task
# def fetch_and_process_handball():
#     """
#     Task to fetch and process matches.
#     Task will run every minute.
#     """
#     print("started handball")
#     matches = fetch_matches("handball")
#     print("handball matches fetched ", len(matches))
#     process_favourites(matches)
#     print("handball matches processed")
    


def fetch_matches(url, sport_id):
    """
    Fetch today matches for a given sport.
    Extract necessary details of events from the response.
    Return the list of dictionaries with match details.
    """

    # Getting the current date
    response = requests.get(url)
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
        match["away_team_name"] = event.get("awayTeam").get("name")
        match["home_team_id"] = event.get("homeTeam").get("id")
        match["away_team_id"] = event.get("awayTeam").get("id")
        match["home_score"] = event.get("homeScore").get("period1", 0)
        match["away_score"] = event.get("awayScore").get("period1", 0) 
            
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
    Process each match concurrently using a thread pool.
    """
    with ThreadPoolExecutor(max_workers=30) as executor:
        # submit each match for processing
        futures = [executor.submit(process_single_match, match) for match in matches]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing match: {e}")

def process_single_match(match):
    """
    Insert the favourite team and odds in redis if match has not started yet.
    If the match is at (halftime, firstset, keyevent) of (Basketball, Tennis, Handball) 
    and favourite is losing, generate an alert and delete favourite from redis.
    """
    
    event_id = match["event_id"]
    
    # Create a key name for the favourite data
    favourite_key = f"favourite:{event_id}"
    
    # if match is not started and favourite is not present in redis insert favourite
    if not r.exists(favourite_key) and match["status"] == "Not started":
        
        # fetch odds for the event
        markets = fetch_odds(event_id)
        
        if not markets:
            return
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
            r.set(favourite_key, json.dumps(favourite_data), ex=90000)
       
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
            
    # For tennis if favourite loses the first half set, remove from redis
    elif match["status"] == "2nd set":
        if r.exists(favourite_key):
            stored_data = json.loads(r.get(favourite_key))
            
            # check if favourite is losing
            if stored_data["favourite"] == "home":
                if match["home_score"] < match["away_score"]:
                    message = f"Favourite {match['home_team_name']} lost the first set."
                    send_alert(match, stored_data, message)
                    
            elif stored_data["favourite"] == "away":
                if match["away_score"] < match["home_score"]:
                    message = f"Favourite {match['away_team_name']} lost the first set."
                    send_alert(match, stored_data, message)
                    
            # In any case delete favourite from the redis
            r.delete(favourite_key)
    
def send_alert(match, stored_data, message):
    """
    Send the alert to telegram to all the valid users.
    """
    
    event_id = match["event_id"]
    
    # Fetch current odds
    markets = fetch_odds(event_id)
    if markets:
        if match["sport_id"] == "basketball":
            home_odds_frac = markets[0].get("choices")[0].get("fractionalValue")
            away_odds_frac = markets[0].get("choices")[1].get("fractionalValue")
        elif match["sport_id"] == "tennis":
            home_odds_frac = markets[1].get("choices")[0].get("fractionalValue")
            away_odds_frac = markets[1].get("choices")[1].get("fractionalValue")
            
            
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