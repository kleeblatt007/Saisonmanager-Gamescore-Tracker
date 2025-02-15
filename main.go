package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type Game struct {
	GameID       int    `json:"game_id"`
	HomeTeamName string `json:"home_team_name"`
}

type GameResult struct {
	Result struct {
		HomeGoals  int `json:"home_goals"`
		GuestGoals int `json:"guest_goals"`
	} `json:"result"`
}

func getCurrentGameID() int {
	url := "https://saisonmanager.de/api/v2/leagues/1584/game_days/current/schedule.json"
	resp, err := http.Get(url)
	if err != nil {
		return -1
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return -1
	}

	var games []Game
	err = json.Unmarshal(body, &games)
	if err != nil {
		return -1
	}

	for _, game := range games {
		if game.HomeTeamName == "Berlin Rockets" {
			return game.GameID
		}
	}
	return -1
}

func getGameScore(gameID int) (int, int) {
	url := fmt.Sprintf("https://saisonmanager.de/api/v2/games/%d.json", gameID)
	resp, err := http.Get(url)
	if err != nil {
		return -1, -1
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return -1, -1
	}

	var gameResult GameResult
	err = json.Unmarshal(body, &gameResult)
	if err != nil {
		return -1, -1
	}

	return gameResult.Result.HomeGoals, gameResult.Result.GuestGoals
}

func writeGameScoreToFile(homeGoals, guestGoals int) {
	file, err := os.Create("gamescore.txt")
	if err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}
	defer file.Close()

	_, err = file.WriteString(fmt.Sprintf("%d:%d", homeGoals, guestGoals))
	if err != nil {
		fmt.Println("Error writing to file:", err)
	}
}

func main() {
	gameID := getCurrentGameID()
	if gameID == -1 {
		fmt.Println("No game found")
		os.Exit(1)
	}

	for {
		homeGoals, guestGoals := getGameScore(gameID)
		fmt.Printf("Home: %d, Guest: %d\n", homeGoals, guestGoals)
		writeGameScoreToFile(homeGoals, guestGoals)
		time.Sleep(20 * time.Second)
	}
}
