# NHL Data Platform — Data Dictionary

DuckDB warehouse: `warehouse/nhl.duckdb`. Seasons **2010-11 to 2025-26** (`season` is an integer in
`YYYYYYYY` form, e.g. `20232024`). Open it read-only for analysis:

```python
import duckdb
con = duckdb.connect("warehouse/nhl.duckdb", read_only=True)
df = con.execute("SELECT * FROM analytics.team_game_log").df()
```

Schemas follow raw → staging → analytics. **For ML, start from `analytics.*_game_log`.**

## analytics (start here)

All three logs are one row per entity per game, regular season (`game_type = 2`) and playoffs
(`game_type = 3`). They only contain finished games with a boxscore. Filter on `game_type` as needed.
They hold **observed game results only** — no features. When building features for prediction, only
use data from games strictly before the one being predicted.

| Table | Grain | Key |
|---|---|---|
| `analytics.team_game_log` | team × game | `(game_id, team)` |
| `analytics.skater_game_log` | skater × game | `(game_id, player_id)` |
| `analytics.goalie_game_log` | goalie × game | `(game_id, player_id)` |
| `analytics.team_season_stats` | team × season (regular season) | `(season, team)` |
| `analytics.team_stats` | team × season (regular season, legacy) | `(season, team)` |

### team_game_log
`game_id, season, game_type, game_date, team, opponent, is_home, goals_for, goals_against, sog_for,
sog_against, last_period_type (REG/OT/SO), result (W/L/OTL), points (2/1/0)`.
Each game appears twice (one row per team). `result = 'OTL'` means lost in overtime or shootout.

### skater_game_log
Team-game columns (`game_id, season, game_type, game_date, team, opponent, is_home`) plus
`player_id, player_name, position (C/L/R/D), goals, assists, points, plus_minus, pim, hits,
power_play_goals, sog, faceoff_win_pct, toi_seconds, blocked_shots, shifts, giveaways, takeaways`.

### goalie_game_log
Team-game columns plus `player_id, player_name, toi_seconds, starter, decision (W/L/O), shots_against,
saves, goals_against, save_pct, even_strength_goals_against, power_play_goals_against,
shorthanded_goals_against, pim`.

### team_season_stats
`season, team, games_played, wins, regulation_losses, overtime_losses, points, goals_for,
goals_against, sog_for, sog_against`. `analytics.team_stats` is the older version (wins/losses only,
losses include overtime losses).

## staging
`staging.regular_season_games`, `staging.playoff_games`: finished games (`game_state = 'OFF'`) from
the schedule, with `winner`. Columns: `game_id, season, game_date, venue_name, home_team_abbrev,
home_score, away_team_abbrev, away_score, winner`.

## raw
Loaded as-is from the NHL API JSON files in `data/raw/`.
- `raw.games` — schedule, one row per game (`game_id` PK), includes preseason (`game_type = 1`) and
  unfinished games.
- `raw.boxscore_team`, `raw.boxscore_skaters`, `raw.boxscore_goalies` — boxscore data per game.
- `raw.pipeline_runs` — seasons whose schedule has been loaded.

`game_type`: 1 preseason, 2 regular season, 3 playoffs.

## Caveats for modelling
- **2012-13** was shortened by a lockout (48 games per team).
- **2019-20** was suspended in March 2020 (~1082 regular-season games); its playoffs were played in
  a bubble with neutral sites.
- **2020-21** was shortened to 56 games with a realigned division format.
- Franchise changes: Arizona (`ARI`) became Utah (`UTA`) in 2024-25; Seattle (`SEA`) joined in
  2021-22; Vegas (`VGK`) joined in 2017-18. Atlanta (`ATL`) became Winnipeg (`WPG`) in 2011-12.
- Team abbreviations in the logs are the abbreviations used by the API at the time of the game.

## Example queries
```sql
-- Home win rate per season
SELECT season, AVG((result = 'W')::INT) AS home_win_rate
FROM analytics.team_game_log
WHERE is_home AND game_type = 2
GROUP BY season ORDER BY season;

-- Top scorers of a season
SELECT player_name, SUM(points) AS points
FROM analytics.skater_game_log
WHERE season = 20232024 AND game_type = 2
GROUP BY player_id, player_name ORDER BY points DESC LIMIT 10;

-- Rest days between games for each team
SELECT game_id, team,
       date_diff('day', LAG(game_date) OVER (PARTITION BY team ORDER BY game_date), game_date)
         AS days_since_last_game
FROM analytics.team_game_log;
```

## Validation
`make validate` runs consistency checks (all seasons present, every finished game has a boxscore,
boxscore goals equal the schedule score, no duplicate player rows).
