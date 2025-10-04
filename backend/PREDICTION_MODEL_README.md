# NFL Player Performance Prediction Model

## Overview

This predictive model forecasts NFL player performance using statistical analysis and machine learning techniques. The model predicts:
- **Yardage benchmark probabilities** (15, 25, 40, 50, 65, 75, 100, 125, 150 yards)
- **Touchdown probability** (likelihood of scoring at least one TD)

The predictions leverage historical player performance, opponent defensive statistics, consistency metrics, and time-weighted analysis to provide accurate forecasts.

---

## Model Architecture

### 1. **Time-Weighted Performance Analysis**

The model prioritizes recent performance over historical data using a sophisticated weighting system:

#### Current Season Weighting
- **Current season games**: 2.0x weight multiplier
- **Previous seasons**: Exponential decay at 70% per season
  - 1 season ago: 0.7x weight
  - 2 seasons ago: 0.49x weight
  - 3 seasons ago: 0.343x weight

#### Weekly Recency Weighting (Within Current Season)
- **Most recent week**: 1.0x weight
- **Weekly decay**: 5% reduction per week back
- Formula: `weight *= (0.95 ^ weeks_ago)`

**Example:**
- Week 4 game (current): 2.0x weight
- Week 3 game (1 week ago): 2.0 * 0.95 = 1.9x weight
- Week 2 game (2 weeks ago): 2.0 * 0.95² = 1.805x weight

This ensures the model adapts quickly to recent trends while maintaining historical context.

---

### 2. **Player Consistency Metrics**

#### Weighted Standard Deviation
Calculates performance variance using time-weighted values:
```python
weighted_variance = Σ(weights * (values - weighted_mean)²) / Σ(weights)
weighted_std = √weighted_variance
```

#### Consistency Score
Normalized metric (0-1 scale) measuring performance reliability:
```python
consistency_score = 1 / (1 + std_dev / mean)
```
- **Score → 1**: Highly consistent (low variance)
- **Score → 0**: Highly volatile (high variance)

**Use Case:** Helps identify "boom-bust" vs reliable players for betting strategies.

---

### 3. **Yardage Benchmark Predictions**

#### Statistical Model: Normal Distribution

The model assumes player yardage follows a normal distribution based on weighted historical performance.

**Steps:**

1. **Calculate Weighted Player Mean**
   ```python
   weighted_mean = Σ(weights * yardage_values) / Σ(weights)
   ```

2. **Adjust for Opponent Defense**
   ```python
   league_average = 250 yards (passing) or 120 yards (rushing)
   defensive_factor = opponent_avg_allowed / league_average
   adjusted_mean = player_weighted_mean * defensive_factor
   ```

3. **Calculate Probabilities Using Normal CDF**
   ```python
   z_score = (benchmark - adjusted_mean) / weighted_std
   probability = 1 - Φ(z_score)  # Φ = normal CDF
   ```

**Example Calculation (WR with 85 avg yards, 30 std dev):**
- P(50+ yards) = P(Z > (50-85)/30) = P(Z > -1.17) = **87.9%**
- P(100+ yards) = P(Z > (100-85)/30) = P(Z > 0.5) = **30.8%**

#### Defensive Adjustment Factor

**Important: Current Season Data Only**

The model uses **current season defensive statistics only** because defensive performance fluctuates significantly year-to-year due to:
- Personnel changes (free agency, draft picks, retirements)
- Scheme changes (new defensive coordinators)
- Injuries to key defensive players
- Overall team strength variations

When opponent defensive data is available:
```python
if opponent_allows_280_passing_yards and league_avg_is_250:
    defensive_factor = 280/250 = 1.12
    adjusted_projection = 85 * 1.12 = 95.2 yards
```

This increases probabilities against weak defenses and decreases them against strong defenses.

**Defensive Data Sources:**
- **Points Allowed**: Extracted from NFL schedules (home/away scores)
- **Yards Allowed**: Calculated from play-by-play data aggregation
  - Passing yards allowed: Sum of passing yards when team is on defense
  - Rushing yards allowed: Sum of rushing yards when team is on defense
  - Total yards allowed: Sum of all yards gained against defense

---

### 4. **Touchdown Probability Prediction**

#### Statistical Model: Poisson Distribution

Touchdown scoring events are modeled as rare events following a Poisson distribution.

**Steps:**

1. **Calculate Weighted TD Rate**
   ```python
   weighted_td_avg = Σ(weights * td_per_game) / Σ(weights)
   ```

2. **Adjust for Opponent Defense (Current Season Only)**
   ```python
   league_avg_points = 22 points/game
   td_factor = opponent_points_allowed / league_avg_points
   adjusted_td_rate = player_td_avg * td_factor
   ```

   Note: Only uses current season defensive points allowed data, as defensive performance varies significantly year-to-year.

3. **Calculate Probability Using Poisson**
   ```python
   P(X ≥ 1) = 1 - P(X = 0)
   P(X = 0) = e^(-λ) where λ = adjusted_td_rate
   td_probability = 1 - e^(-adjusted_td_rate)
   ```

**Example Calculation (Player averages 0.5 TDs/game):**
- Against average defense: P(TD) = 1 - e^(-0.5) = **39.3%**
- Against weak defense (1.15x factor): P(TD) = 1 - e^(-0.575) = **43.7%**
- Against strong defense (0.85x factor): P(TD) = 1 - e^(-0.425) = **34.6%**

---

## Defensive Statistics Integration

### Data Collection Process

The model integrates real-time defensive statistics from the current NFL season to improve prediction accuracy. Defensive data is collected from two primary sources:

#### 1. **Points Allowed** (from NFL Schedules)
```python
# Extract points allowed from game results
home_games: away_score = points_allowed
away_games: home_score = points_allowed
```

#### 2. **Yards Allowed** (from Play-by-Play Data)
```python
# Aggregate yards when team is on defense (defteam)
passing_yards_allowed = sum(pbp[defteam == 'BAL']['passing_yards'])
rushing_yards_allowed = sum(pbp[defteam == 'BAL']['rushing_yards'])
total_yards_allowed = sum(pbp[defteam == 'BAL']['yards_gained'])
```

### Current Season Focus

**Why Current Season Only?**

Defensive performance is highly volatile year-over-year due to:
- **Personnel Turnover**: Free agency, retirements, draft picks
- **Coaching Changes**: New defensive coordinators with different schemes
- **Injuries**: Key defensive players missing significant time
- **Overall Team Strength**: Changes in offense affecting defensive time on field

**Data Shows:**
- 2023 #1 defense may rank #20 in 2024
- Year-over-year correlation for team defense: ~0.35 (weak)
- Current season data provides more accurate predictions

### Defensive Stats Available (2024 Season)

**Database Contains:**
- 32 NFL teams
- 570 total defensive stat records
- Average 19 games per team (full season + playoffs)

**Example: Baltimore Ravens (2024)**
- Passing Yards Allowed: 256.1 per game
- Rushing Yards Allowed: 80.9 per game
- Points Allowed: 21.2 per game

### Syncing Defensive Data

```bash
# Sync current season defensive statistics
cd backend
python sync_current_defense.py
```

This script:
1. Imports all NFL teams to database
2. Fetches schedules and play-by-play data for current season
3. Calculates defensive statistics per team per week
4. Stores in `team_stats` table with weekly granularity

---

## API Endpoints

### 1. Complete Player Prediction
```http
GET /api/predictions/player/{player_id}?opponent={TEAM_ABBR}
```

**Response:**
```json
{
  "success": true,
  "prediction": {
    "player": {
      "id": 611,
      "name": "J.Chase",
      "position": "WR",
      "team": "CIN"
    },
    "opponent": "BAL",
    "stat_type": "receiving_yards",
    "yardage_predictions": {
      "projected_yards": 87.8,
      "player_avg": 87.8,
      "opponent_avg_allowed": 245.2,
      "consistency_score": 0.59,
      "probabilities": {
        "15": 88.33,
        "25": 84.8,
        "40": 78.31,
        "50": 73.2,
        "65": 64.57,
        "75": 58.32,
        "100": 42.12,
        "125": 27.17,
        "150": 15.46
      }
    },
    "touchdown_prediction": {
      "td_probability": 52.1,
      "avg_tds_per_game": 0.74,
      "player_td_avg": 0.74,
      "consistency": 0.46
    }
  }
}
```

### 2. Yardage Probabilities Only
```http
GET /api/predictions/yardage/{player_id}?opponent={TEAM_ABBR}&stat_type={receiving_yards|rushing_yards|total_yards}
```

### 3. Touchdown Probability Only
```http
GET /api/predictions/touchdown/{player_id}?opponent={TEAM_ABBR}&position={WR|RB|TE}
```

---

## Technical Implementation

### Dependencies
```
scipy==1.11.4      # Statistical distributions (norm, poisson)
numpy==1.26.2      # Numerical computations
sqlalchemy==2.0.23 # Database queries
```

### Key Classes

#### `PredictionService`
Main service class handling all predictions.

**Methods:**
- `calculate_time_weights(games_data, current_season, current_week)` → Calculate time-based weights
- `get_player_stats_weighted(player_id, stat_type, limit)` → Get weighted player stats
- `get_defensive_stats(team_abbr, stat_type, current_season_only=True)` → Get opponent defense stats (current season only)
- `predict_yardage_probabilities(player_id, opponent_team, stat_type)` → Yardage predictions
- `predict_touchdown_probability(player_id, opponent_team, position)` → TD predictions
- `get_player_prediction(player_id, opponent_team)` → Complete prediction

#### `NFLDataService`
Handles fetching and syncing NFL data from external sources.

**Methods:**
- `fetch_team_stats(seasons)` → Fetch defensive stats from schedules (points) and play-by-play (yards)
- `import_teams_to_db()` → Import all NFL teams to database
- `import_team_stats_to_db(team_stats_df)` → Import defensive statistics to database
- `sync_all_data(years)` → Complete data sync including teams, players, and defensive stats

**Defensive Stats Sync:**
```bash
# Sync current season defensive data only
python sync_current_defense.py
```

### Database Schema

**Required Tables:**
1. **players** - Player information (id, name, position, team)
2. **player_stats** - Weekly player statistics (season, week, yards, TDs)
3. **teams** - Team information (id, team_abbr, team_name)
4. **team_stats** - Weekly defensive statistics (season, week, yards_allowed, points_allowed)

---

## Model Strengths

### ✅ Advantages

1. **Adaptive to Recent Performance**
   - Time weighting ensures model responds to hot/cold streaks
   - Current season 2x weight captures current form

2. **Opponent-Aware**
   - Adjusts predictions based on defensive matchups
   - Differentiates between elite and weak defenses

3. **Consistency Measurement**
   - Identifies reliable vs volatile players
   - Helps assess risk for betting strategies

4. **Probabilistic Output**
   - Provides probabilities rather than binary predictions
   - Allows for expected value calculations

5. **Position-Specific Logic**
   - WR/TE use receiving yards, RB uses rushing yards
   - Different TD probability models by position

### ⚠️ Limitations

1. **Current Season Defensive Data Only**
   - Uses only current season defensive stats (defenses fluctuate year to year)
   - Early season may have limited defensive sample size
   - Falls back to player-only analysis if defensive data unavailable

2. **Assumes Normal Distribution**
   - Yardage may not always follow normal curve
   - Extreme outliers can skew predictions

3. **No Game Context**
   - Doesn't account for weather, injuries, game script
   - Home/away splits not yet implemented

4. **Limited Historical Depth**
   - Uses last 20 games by default
   - Rookies have limited data

5. **Season Transition Period**
   - Model currently configured for 2024 season data
   - Requires update when new season data becomes available

---

## Future Enhancements

### Planned Features

1. **Enhanced Contextual Factors**
   - Weather conditions (wind, rain impact passing)
   - Home/away performance splits
   - Division rivalry adjustments

2. **Game Script Analysis**
   - Team implied totals (over/under)
   - Vegas spread impact on volume
   - Pace of play adjustments

3. **Machine Learning Upgrade**
   - Gradient boosting models (XGBoost, LightGBM)
   - Feature importance analysis
   - Cross-validation for accuracy testing

4. **Player Props Integration**
   - Compare model predictions to Vegas lines
   - Calculate expected value (EV)
   - Identify +EV betting opportunities

5. **Ensemble Methods**
   - Combine multiple model approaches
   - Weighted averaging of predictions
   - Confidence intervals

6. **Real-time Updates**
   - Injury report adjustments
   - Lineup changes (backup RB gets start)
   - Live in-game predictions

---

## Usage Examples

### Example 1: Wide Receiver vs Above-Average Passing Defense
```python
# Player: Ja'Marr Chase (87.8 avg yards, 2024 season)
# Opponent: BAL (allows 256.1 passing yards/game vs 250 league avg)

defensive_factor = 256.1 / 250 = 1.024
projected = 87.8 * 1.024 = 90.0 yards

# Real 2024 data results:
P(50+ yards): 73.2% → 74.3% (slight increase)
P(100+ yards): 42.1% → 43.5% (slight increase)
TD Probability: 52.1% → 50.7% (adjusted for BAL allowing 21.2 pts/game)
```

### Example 2: Running Back vs Elite Run Defense
```python
# Player: RB averaging 85 rushing yards
# Opponent: Allows only 90 rushing yards (vs 120 league avg)

defensive_factor = 90 / 120 = 0.75
projected = 85 * 0.75 = 63.8 yards

# Probabilities decrease
P(50+ yards): 75% → 58%
P(100+ yards): 35% → 12%
```

### Example 3: Touchdown Probability Analysis
```python
# Player: TE averaging 0.6 TDs/game
# Opponent: Allows 28 points/game (vs 22 league avg)

td_factor = 28 / 22 = 1.27
adjusted_rate = 0.6 * 1.27 = 0.76

P(TD) = 1 - e^(-0.76) = 53.2% (vs 45.1% against average)
```

---

## Model Validation

### Accuracy Metrics (To Be Implemented)

1. **Calibration Analysis**
   - Compare predicted probabilities to actual outcomes
   - 50% prediction should hit ~50% of the time

2. **Brier Score**
   - Measures prediction accuracy (0 = perfect, 1 = worst)
   - Target: < 0.20 for well-calibrated model

3. **ROC-AUC**
   - Evaluates classification performance
   - Target: > 0.70 for useful predictions

4. **Backtesting**
   - Test predictions on historical games
   - Calculate profit/loss on hypothetical bets

---

## Contributing

### Adding New Features

1. Update `PredictionService` class in `services/prediction_service.py`
2. Add corresponding API endpoint in `routes/prediction_routes.py`
3. Update this README with new methodology
4. Add unit tests for validation

### Model Improvements

- Submit pull requests with backtesting results
- Include statistical justification for changes
- Provide performance comparisons (before/after)

---

## License & Disclaimer

⚠️ **Disclaimer**: This model is for educational and analytical purposes only. Sports betting involves risk and this model does not guarantee profits. Always gamble responsibly.

---

## Contact & Support

For questions, issues, or feature requests, please open an issue on the GitHub repository.

**Model Version**: 1.0.0
**Last Updated**: October 2025
**Maintained By**: Football Betting Analytics Team
