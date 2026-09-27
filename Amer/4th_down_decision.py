import sys
 
import nflreadpy as nfl
import pandas as pd
 
SEASON = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
 
pbp = nfl.load_pbp(seasons=[SEASON]).to_pandas()
 
# Real 4th-down decisions only: go for it, punt, or field goal
fourth = pbp[
    (pbp["down"] == 4)
    & (pbp["play_type"].isin(["run", "pass", "punt", "field_goal"]))
    & (pbp["qb_kneel"].fillna(0) != 1)
    & (pbp["qb_spike"].fillna(0) != 1)
].copy()
 
fourth["decision"] = fourth["play_type"].map(
    {"run": "go", "pass": "go", "punt": "punt", "field_goal": "field_goal"}
)
 
# fourth_down_converted is only meaningful when the team went for it
fourth.loc[fourth["decision"] != "go", "fourth_down_converted"] = pd.NA
 
cols = [
    "game_id", "season", "week", "season_type", "posteam", "defteam",
    "qtr", "game_seconds_remaining", "half_seconds_remaining",
    "yardline_100", "ydstogo", "score_differential",
    "posteam_timeouts_remaining", "defteam_timeouts_remaining",
    "wp", "vegas_wp", "spread_line",
    "play_type", "decision", "fourth_down_converted", "fourth_down_failed",
    "yards_gained", "epa", "wpa", "penalty", "desc",
]
fourth = fourth[[c for c in cols if c in fourth.columns]].reset_index(drop=True)
 
out = f"fourth_downs_{SEASON}.csv"
fourth.to_csv(out, index=False)
 
print(f"Season {SEASON}: {len(fourth):,} fourth-down decisions -> {out}")
print(fourth["decision"].value_counts())
go = fourth[fourth["decision"] == "go"]
print(f"Go-for-it rate: {len(go) / len(fourth):.1%}")
print(f"Conversion rate when going: {go['fourth_down_converted'].astype(float).mean():.1%}")