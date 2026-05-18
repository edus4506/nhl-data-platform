import requests

BASE_URL = "https://api-web.nhle.com/v1"


def fetch_teams_for_season(season: str) -> list[str]:
	year = season[:4]
	date = f"{year}-12-01"

	url = f"{BASE_URL}/standings/{date}"
	response = requests.get(url, timeout=30)
	response.raise_for_status()

	data = response.json()
	return [team["teamAbbrev"]["default"] for team in data["standings"]]


def main() -> None:
	season = "20102011"
	teams = fetch_teams_for_season(season)
	print(f"Teams in {season} : {len(teams)}")
	print(teams)


if __name__ == "__main__":
	main()
