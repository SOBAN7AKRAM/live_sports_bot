import requests
import time

API_KEY = "dPlMFyLnhvkwcOkVeqYoSI370uIHHUFxyzxFGTcr"
SPORT = "tennis"  # Change this to "basketball" if needed
TIER = "trial"
LANG = "en"

def fetch_live_games():
    url = f"https://api.sportradar.com/tennis/trial/v3/en/schedules/2025-02-02/summaries.json?api_key=dPlMFyLnhvkwcOkVeqYoSI370uIHHUFxyzxFGTcr"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None


def extract_match_details(json_data):
    matches = []
    for summary in json_data.get("summaries", []):
        # Extract basic event info
        event = summary.get("sport_event", {})
        competitors = event.get("competitors", [])
        status = summary.get("sport_event_status", {})
        
        # Get player/team names and countries
        home = next((c for c in competitors if c.get("qualifier") == "home"), {})
        away = next((c for c in competitors if c.get("qualifier") == "away"), {})
        
        # Handle doubles matches
        def format_competitor(comp):
            if "players" in comp:  # Doubles match
                players = " & ".join([p["name"].split()[0] for p in comp.get("players", [])])
                return f"{players} ({comp.get('country', '')})"
            return f"{comp.get('name', 'Unknown')} ({comp.get('country', '')})"

        home_name = format_competitor(home)
        away_name = format_competitor(away)
        
        # Get scores
        score = f"{status.get('home_score', 0)} - {status.get('away_score', 0)}"
        
        # Get set scores if available
        set_scores = []
        for period in status.get("period_scores", []):
            set_scores.append(f"{period['home_score']}-{period['away_score']}")
        
        # Determine winner
        winner_id = status.get("winner_id")
        winner = next((c for c in competitors if c["id"] == winner_id), {}).get("name", "Unknown")
        
        # Create match summary
        match = {
            "match": f"{home_name} vs {away_name}",
            "score": score,
            "sets": " | ".join(set_scores) if set_scores else "No set scores",
            "result": f"Winner: {winner}",
            "status": status.get("winning_reason", "completed")
        }
        matches.append(match)
    
    return matches

# # Usage example:
# matches = extract_match_details(fetch_live_games())
# for i, match in enumerate(matches, 1):
#     print(f"Match {i}:")
#     print(f"  Teams: {match['match']}")
#     print(f"  Final Score: {match['score']}")
#     print(f"  Set Scores: {match['sets']}")
#     print(f"  Result: {match['result']}")
#     print(f"  Status: {match['status'].capitalize()}\n")