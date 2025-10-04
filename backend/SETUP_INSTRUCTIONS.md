# Backend Setup Instructions

## Prerequisites

1. **Python 3.8+** installed
2. **PostgreSQL** installed and running
3. **Git** (already configured)

## Step-by-Step Setup

### 1. Install PostgreSQL (if not already installed)

**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Run installer and follow prompts
- Remember the password you set for the `postgres` user

### 2. Create the Database

Open PostgreSQL command line (psql) or pgAdmin and run:

```sql
CREATE DATABASE football_betting;
```

Or use command line:
```bash
psql -U postgres
CREATE DATABASE football_betting;
\q
```

### 3. Set Up Python Virtual Environment

Open terminal in the `backend` folder:

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example environment file:

```bash
copy .env.example .env
```

Edit `.env` file with your database credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_betting
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
```

### 6. Initialize Database and Load Data

Run the setup script to create tables and load initial data:

```bash
python setup_db.py
```

This will:
- Create all database tables
- Fetch 5 years of NFL player statistics
- Import all data into your database
- **Note:** This may take 5-10 minutes depending on your internet connection

### 7. Start the Application

```bash
python app.py
```

The API will be available at: `http://localhost:5000`

### 8. Test the API

Open your browser or use curl to test:

**Health Check:**
```
http://localhost:5000/api/health
```

**Get Current Season Players:**
```
http://localhost:5000/api/players/current-season
```

**Get Data Status:**
```
http://localhost:5000/api/data/status
```

## Available API Endpoints

### Players
- `GET /api/players` - Get all players (with optional filters)
- `GET /api/players/:id` - Get specific player
- `GET /api/players/:id/stats` - Get player statistics
- `GET /api/players/:id/stats/summary` - Get player stats summary
- `GET /api/players/current-season` - Get current season player rankings

### Data Management
- `POST /api/data/sync` - Manually trigger data sync
- `GET /api/data/status` - Get database statistics

## Automatic Updates

The application automatically updates player statistics daily at 6 AM. You can change this in `config.py` by modifying the `UPDATE_STATS_HOUR` setting.

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check your `.env` credentials
- Ensure the database `football_betting` exists

### Import Error for nfl_data_py
- Make sure you activated the virtual environment
- Try: `pip install --upgrade nfl-data-py`

### Slow Data Sync
- The initial sync fetches 5 years of data and may take time
- This is normal for the first run
- Subsequent syncs will be faster as they only update recent data

## Next Steps

Once the backend is running, you can:
1. Test the API endpoints
2. Set up the React frontend
3. Start building the ML prediction model
