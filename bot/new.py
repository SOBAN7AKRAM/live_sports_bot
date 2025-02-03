import requests
import time

API_KEY = "dPlMFyLnhvkwcOkVeqYoSI370uIHHUFxyzxFGTcr"
SPORT = "tennis"  # Change this to "basketball" if needed
TIER = "trial"
LANG = "en"

def fetch_live_games():
    url = f"https://api.sportradar.com/{SPORT}/{TIER}/v2/{LANG}/schedules/live/timelines_delta.json?api_key={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def fetch_game_summary(game_id):
    url = f"https://api.sportradar.com/{SPORT}/{TIER}/v2/{LANG}/games/{game_id}/summary.json?api_key={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Demo loop
while True:
    live_games = fetch_live_games()
    
    # if live_games and "summaries" in live_games:
    #     print("Live games found!")
    #     for game in live_games["summaries"]:
    #         game_id = game["sport_event"]["id"]
    #         summary = fetch_game_summary(game_id)
    #         print(game_id, summary)
    #         if summary:
    #             # Extract team names and scores from the summary
    #             print("summary found")
    #             sport_event = summary.get("game", {})
    #             status_info = summary.get("game", {}).get("status", {})
                
    #             # Example: Get teams and scores from summary structure (adjust as needed)
    #             # This is just an example; you'll need to adapt it to the actual summary structure.
    #             # For the sample data, scores are available under "sport_event_status"
    #             home_team = game["sport_event"]["competitors"][0]["name"]
    #             away_team = game["sport_event"]["competitors"][1]["name"]
    #             home_score = game["sport_event_status"]["home_score"]
    #             away_score = game["sport_event_status"]["away_score"]
    #             match_status = game["sport_event_status"]["match_status"]
                
    #             print(f"\n🚨 Live Update: {home_team} vs {away_team}")
    #             print(f"🏀 Score: {home_score} - {away_score}")
    #             print(f"⏱️ Status: {match_status}")
                
    #             # Optional: If the summary contains events, show the latest event
    #             if "events" in summary.get("game", {}) and len(summary["game"]["events"]) > 0:
    #                 latest_event = summary["game"]["events"][-1]["description"]
    #                 print(f"📢 Latest Event: {latest_event}")
    for game in live_games['sport_event_timeline_deltas']:
        status = game['sport_event_timeline']['sport_event_status']['status']
        if status == 'live':
            match_status = game['sport_event_timeline']['sport_event_status']['match_status']
            home_score = game['sport_event_timeline']['sport_event_status']['home_score']
            away_score = game['sport_event_timeline']['sport_event_status']['away_score']
            time_remaining = game['sport_event_timeline']['sport_event_status']['clock']['remaining']

            print(f"Status: {status}")
            print(f"Quarter: {match_status}")
            print(f"Score: Home {home_score} - Away {away_score}")
            print(f"Time Remaining: {time_remaining}")
            print("\n")

    else:
        print("No live games currently.")
    
    time.sleep(60)  # Poll every 60 seconds
