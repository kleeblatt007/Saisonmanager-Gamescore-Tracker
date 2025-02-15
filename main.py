import sys
import requests
import json
import time
import os

def getCurrentGameId() -> int:
    url = "https://saisonmanager.de/api/v2/leagues/1584/game_days/current/schedule.json"
    try:
        res = requests.get(url)
        data = json.loads(res.text)
        for game in data:
            if(game["home_team_name"] == "Berlin Rockets"):
                return game["game_id"]
        return -1
    except:
        return -1

def getGameScore(gameId: int) -> tuple:
    url = f"https://saisonmanager.de/api/v2/games/{gameId}.json"
    try:
        res = requests.get(url)
        data = json.loads(res.text)["result"]
        return (data["home_goals"], data["guest_goals"])
    except:
        return (-1, -1)
    
def get_resource_path(filename) -> str:
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    elif __file__:
        path = os.path.dirname(__file__)
    print(f"Path of txt: {path}")
    return os.path.join(path, filename)
    
def writeGameScoreToFile(home_goals: int, guest_goals: int) -> None:
    file_path = get_resource_path("gamescore.txt")
    with open(file_path, "w") as f:
        f.write(f"{home_goals}:{guest_goals}")

def main() -> int:
    gameId = getCurrentGameId()
    if(gameId == -1):
        print("No game found")
        return -1
    
    # starttime = time.monotonic()
    last_score = None
    while True:
        home_goals, guest_goals = getGameScore(gameId)
        print(f"Current score: {home_goals}:{guest_goals}")
        if (home_goals, guest_goals) != last_score:
            last_score = (home_goals, guest_goals)
            writeGameScoreToFile(home_goals, guest_goals)
        time.sleep(20)

    return 0

if __name__ == "__main__":
    sys.exit(main())