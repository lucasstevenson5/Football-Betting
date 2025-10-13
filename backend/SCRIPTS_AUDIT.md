# Backend Scripts Audit

## Core Application (KEEP)
- `app.py` - Main Flask application
- `config.py` - Configuration

## Data Import/Export (KEEP - Currently Used)
- `export_seed_data.py` - Export database to seed file
- `import_seed_data.py` - Import seed file to database
- `scrape_2025_espn.py` - Import 2025 data from ESPN (used for week 5+)

## Position Fixes (KEEP - Recently Created & Used)
- `consolidate_players.py` - Merge duplicate players (just ran successfully)
- `fix_all_positions.py` - Fix positions from both APIs (just ran successfully)
- `fix_player_positions.py` - Fix ESPN player positions (just ran successfully)
- `fix_2025_rookie_positions.py` - Check 2025 rookies (just ran successfully)
- `position_overrides.py` - Manual position overrides (actively used)

## Deprecated/Redundant Scripts (DELETE)

### Old ESPN Exploration Scripts (no longer needed)
- `check_espn_stats.py` - One-off exploration
- `explore_espn_stats_api.py` - One-off exploration
- `explore_espn_team_defense.py` - One-off exploration
- `explore_espn_defense_detailed.py` - One-off exploration
- `get_espn_game_stats.py` - One-off exploration
- `find_espn_defense_yards.py` - One-off exploration

### Old 2025 Import Scripts (replaced by scrape_2025_espn.py)
- `fetch_espn_2025.py` - Old version
- `simple_espn_2025.py` - Old version
- `import_2025_espn.py` - Old version
- `rescrape_2025.py` - Old one-off

### Old Defense Scripts (functionality now in services/)
- `explore_defense.py` - One-off exploration
- `explore_pbp.py` - One-off exploration
- `sync_2025_defense.py` - Redundant, use API endpoints now
- `sync_current_defense.py` - Redundant, use API endpoints now

### Old Test Scripts (one-off debugging)
- `test_2025_data.py`
- `test_defensive_calcs.py`
- `test_espn_defense_2025.py`
- `test_espn_endpoints.py`
- `test_espn_scoreboard_2025.py`
- `test_espn_yards.py`
- `test_predictions_with_defense.py`

### Old Position/Data Fix Scripts (replaced by new scripts)
- `fix_te_positions.py` - Replaced by fix_all_positions.py
- `verify_positions.py` - One-off check
- `find_duplicates.py` - Replaced by consolidate_players.py
- `update_player_names.py` - One-off fix

### Old Database Scripts (replaced)
- `setup_db.py` - Replaced by migrations
- `init_data.py` - Use import_seed_data.py instead
- `add_passing_columns.py` - One-off migration
- `check_qb_stats.py` - One-off check

## Summary
- **Keep:** 10 scripts (core app + active utilities)
- **Delete:** 29 scripts (exploration, old versions, one-offs)
