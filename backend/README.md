# Football Betting Backend

Flask-based REST API for NFL player statistics and predictions.

## Quick Start

See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for detailed setup guide.

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your database credentials

# Setup database and load data
python setup_db.py

# Run the application
python app.py
```

## Project Structure

```
backend/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── setup_db.py                 # Database initialization script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── models/                    # Database models
│   ├── __init__.py
│   ├── player.py             # Player and PlayerStats models
│   └── team.py               # Team and TeamStats models
├── routes/                    # API endpoints
│   ├── __init__.py
│   ├── player_routes.py      # Player-related endpoints
│   └── data_routes.py        # Data management endpoints
├── services/                  # Business logic
│   ├── __init__.py
│   └── nfl_data_service.py   # NFL data fetching and processing
└── ml/                        # Machine learning (coming soon)
    └── predictor.py          # Statistical models for predictions
```

## Key Features

### 1. Data Models

**Player Model:**
- Stores player information (name, position, team)
- Links to historical statistics

**PlayerStats Model:**
- Weekly statistics (receptions, yards, touchdowns)
- Both receiving and rushing stats
- Historical data for 5 years

**Team Model:**
- NFL team information

**TeamStats Model:**
- Defensive statistics (points/yards against)
- Used for opponent analysis

### 2. Data Service

The `NFLDataService` class handles:
- Fetching data from NFL sources using `nfl_data_py`
- Processing and cleaning data
- Importing data into PostgreSQL
- Automatic daily updates

### 3. API Endpoints

**Player Endpoints:**
- Filter players by position, team, or name
- Get detailed player statistics
- View season summaries and averages
- Rankings for current season

**Data Management:**
- Manual data synchronization
- Database status and health checks

### 4. Automatic Updates

- Scheduled daily updates at 6 AM (configurable)
- Runs in background thread
- Fetches latest player statistics

## Database Schema

### players
```sql
id              SERIAL PRIMARY KEY
player_id       VARCHAR(50) UNIQUE NOT NULL
name            VARCHAR(100) NOT NULL
position        VARCHAR(10) NOT NULL
team            VARCHAR(10) NOT NULL
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### player_stats
```sql
id                      SERIAL PRIMARY KEY
player_id               INTEGER FOREIGN KEY
season                  INTEGER NOT NULL
week                    INTEGER
receptions              INTEGER DEFAULT 0
receiving_yards         INTEGER DEFAULT 0
receiving_touchdowns    INTEGER DEFAULT 0
targets                 INTEGER DEFAULT 0
rushes                  INTEGER DEFAULT 0
rushing_yards           INTEGER DEFAULT 0
rushing_touchdowns      INTEGER DEFAULT 0
opponent                VARCHAR(10)
home_away              VARCHAR(4)
created_at             TIMESTAMP
updated_at             TIMESTAMP
```

## Learning Points

### PostgreSQL & SQLAlchemy
- **Models**: Check `models/player.py` to see how SQLAlchemy ORM maps Python classes to database tables
- **Relationships**: One-to-Many relationship between Player and PlayerStats
- **Indexes**: Composite indexes for efficient querying (player_id + season + week)
- **Migrations**: Using `db.create_all()` for initial setup

### Flask API Design
- **Blueprints**: Organized routes into logical modules
- **Query Parameters**: Filter and pagination support
- **Error Handling**: Try-catch blocks with appropriate HTTP status codes
- **CORS**: Enabled for frontend communication

### Data Processing
- **Pandas**: Used for data manipulation in `nfl_data_service.py`
- **Batch Processing**: Commits in batches for performance
- **Data Validation**: Handling missing values and null checks

### Background Tasks
- **Threading**: Scheduler runs in separate thread
- **Schedule Library**: Simple cron-like scheduling in Python

## Next Steps

1. ✅ Backend API complete
2. ⏳ Build ML prediction model
3. ⏳ Create React frontend
4. ⏳ Integrate predictions with Vegas lines

## Dependencies Explained

- **flask**: Web framework
- **flask-cors**: Enable cross-origin requests from React
- **psycopg2-binary**: PostgreSQL adapter for Python
- **sqlalchemy**: ORM for database operations
- **python-dotenv**: Load environment variables
- **pandas**: Data manipulation
- **numpy**: Numerical operations
- **scikit-learn**: Machine learning (for predictions)
- **nfl-data-py**: Free NFL data source
- **requests**: HTTP library
- **schedule**: Job scheduling
