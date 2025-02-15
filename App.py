import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, ttk, StringVar, Scale, IntVar, Entry, Checkbutton
from threading import Thread
import requests
import json
import datetime

def getGameScore(gameId: int) -> tuple:
    url = f"https://saisonmanager.de/api/v2/games/{gameId}.json"
    try:
        res = requests.get(url)
        data = json.loads(res.text)
        score = (data["result"]["home_goals"], data["result"]["guest_goals"], int(data["current_period_title"]["period"]))
        return (score)
    except:
        return ((-1, -1, -1))

def get_resource_path(filename: str = "") -> str:
    if getattr(sys, 'frozen', False):  # Running as an executable
        path = os.path.dirname(sys.executable)
    else:  # Running as a script
        path = os.path.dirname(__file__)
    print(os.path.join(path, filename))
    return os.path.join(path, filename)

def getLeagues():
    url = "https://saisonmanager.de/api/v2/init.json"
    try:
        res = requests.get(url)
        data = json.loads(res.text)
        gameOperations = data["game_operations"]
        leagues = {}
        for federation in gameOperations:
            for league in federation["top_leagues"]:
                leagues[league["name"]] = league["id"]

        return leagues
    except:
        return []
    
def getCurrentGames(leagueId: str):
    url = f"https://saisonmanager.de/api/v2/leagues/{leagueId}/game_days/current/schedule.json"
    try:
        res = requests.get(url)
        data = json.loads(res.text)
        games = {}
        for game in data:
            games[f"{game['home_team_name']} - {game['guest_team_name']}"] = game['game_id']
        return games
    except:
        return {}

class ScoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Saisonmanager Tracker")
        self.txt_folder = StringVar()  # Default folder for the text file
        self.txt_folder.set(get_resource_path())
        self.latest_score = None
        self.running = False
        self.leagues = getLeagues()
        self.games = {}
        self.selectedGame = None
        self.updateFrequency = IntVar()
        self.updateFrequency.set(20)
        self.splitOutput = IntVar()
        self.splitOutput.set(1)
        self.writePeriodFile = IntVar()
        self.writePeriodFile.set(1)


        # GUI Components

        # Game Selection
        tk.Label(root, text="Select League").grid(row=0, column=0, sticky="W", pady=10)
        self.league_selector = ttk.Combobox(root, values=list(self.leagues.keys()))
        self.league_selector.bind('<<ComboboxSelected>>', self.select_league)
        self.league_selector.grid(row=0, column=1, sticky="W", pady=10)
        tk.Label(root, text="Select Game").grid(row=0, column=2, sticky="W", pady=10)
        self.game_selector = ttk.Combobox(root)
        self.game_selector.bind('<<ComboboxSelected>>', self.select_game)
        self.game_selector.grid(row=0, column=3, sticky="W", pady=10)

        # Output Options
        self.select_folder_btn = tk.Button(root, text="Select Folder", command=self.select_folder, background="blue")
        self.select_folder_btn.grid(row=1, column=0, sticky="W", pady=5)
        self.folder_label = tk.Label(root, textvariable=self.txt_folder)
        self.folder_label.grid(row=1, column=1, columnspan=3, sticky="W", pady=10)
        Checkbutton(root, text="Split Score Output", variable=self.splitOutput).grid(row=2, column=0, sticky="W", pady=10)
        Checkbutton(root, text="Write Period File", variable=self.writePeriodFile).grid(row=2, column=1, sticky="W", pady=10)

        tk.Label(root, text="Set Updatefrequnzy (in seconds)").grid(row=3, column=0, sticky="W", pady=0)
        self.scale = Scale(root, from_=5, to=60, orient=tk.HORIZONTAL, variable=self.updateFrequency, length=200)
        self.scale.grid(row=3, column=1, sticky="W", pady=15)
        self.scaleEntry = Entry(root, textvariable=self.updateFrequency, width=3)
        self.scaleEntry.grid(row=3, column=2, sticky="W", pady=0)

        # Control Buttons
        self.start_btn = tk.Button(root, text="Start Tracking", command=self.start_tracking, state= tk.DISABLED)
        self.start_btn.grid(row=4, column=0, sticky="W", pady=10)
        self.stop_btn = tk.Button(root, text="Stop Tracking", command=self.stop_tracking, state=tk.DISABLED)
        self.stop_btn.grid(row=4, column=1, sticky="W", pady=10)

        # Logging
        self.logging_text = tk.Text(root, height=12, width=150, yscrollcommand=True)
        self.logging_text.grid(row=5, column=0, columnspan=4, sticky="W")

    def log(self, message):
        print(f"DEBUG: Logging - {message}")
        try:
            # Use after to update the GUI on the main thread
            self.root.after(0, lambda: self.logging_text.insert(
                tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}\n"))
            self.root.after(0, self.logging_text.see, tk.END)
        except Exception as e:
            print(f"Log Error: {e}")  # Debugging exception
        #self.logging_text.see(tk.END)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.txt_folder.set(folder)

    def select_game(self, event):
        game = self.game_selector.get()
        if game:
            self.selectedGame = self.games[game]
            if self.txt_folder.get():
                self.start_btn.config(state=tk.NORMAL)
    
    def select_league(self, event):
        league = self.league_selector.get()
        if league:
            leagueId = self.leagues[league]
            self.games = getCurrentGames(leagueId)
            self.game_selector.config(values=list(self.games.keys()))
            
    def writeToFile(self, file: str, message: str):
        print("Writing to file: ", file, message)
        file_path = os.path.join(self.txt_folder.get(), file)
        try:
            with open(file_path, "a") as f:
                f.write(f"{message}\n")
                self.log(f"wrote to file {file}: {message}")
        except IOError as e:
            self.log(f"failed to write to file {file}: {e}")

    def writeGameScoreToFile(self, home_goals: int, guest_goals: int, period: int):
        if self.splitOutput.get():
            self.writeToFile("home_goals.txt", home_goals)
            self.writeToFile("guest_goals.txt", guest_goals)
        else:
            self.writeToFile("score.txt", f"{home_goals}:{guest_goals}")
        if(self.writePeriodFile.get()):
            self.writeToFile("period.txt", str(period))

    def track_score(self):
        self.running = True
        while self.running:
            gameScore = getGameScore(self.selectedGame)
            print("Score: ", gameScore)
            #self.root.after(0, lambda: self.log(f"fetched score: {home_goals}:{guest_goals}"))
            #self.root.after(0, lambda: self.logging_text.insert(tk.END, f"fetched score: {home_goals}:{guest_goals}\n"))
            if(gameScore.count(-1) > 0):
                time.sleep(self.updateFrequency.get())
                continue

            if(gameScore != self.latest_score):
                self.latest_score = gameScore
                #self.logging_text.insert(tk.END, f"Current score: {score}\n")
                self.writeGameScoreToFile(gameScore[0], gameScore[1], gameScore[2])
            
            time.sleep(self.updateFrequency.get())  # Wait for 20 seconds before fetching the score again

    def start_tracking(self):
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.tracking_thread = Thread(target=self.track_score, daemon=True)
        self.tracking_thread.start()
        self.log("start tracking")

    def stop_tracking(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("stop tracking")

    def on_close(self):
        self.running = False
        self.root.destroy()

# Main Program
if __name__ == "__main__":
    root = tk.Tk()
    app = ScoreApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)  # Graceful shutdown
    root.mainloop()
