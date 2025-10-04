# Football Betting Analytics App

A full-stack application that uses machine learning to predict NFL player statistics and compare them against Vegas lines to find value bets.

## Features

- **Historical Data**: Ingests 5 years of NFL player and team statistics
- **Machine Learning**: Predicts future player performance using statistical models
- **Real-time Updates**: Automatically fetches and updates player stats
- **Analytics Dashboard**: React-based frontend to visualize current year statistics

## Tech Stack

### Backend
- Python 3.x
- Flask (REST API)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- scikit-learn (Machine Learning)
- nfl-data-py (NFL Stats API)

### Frontend
- React
- Node.js

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database:
- Create a database named `football_betting`
- Update `.env` file with your database credentials

5. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

6. Run the application:
```bash
python app.py
```

### Frontend Setup

Coming soon...

## Project Structure

```
Football-Betting/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── models/                # Database models
│   ├── routes/                # API routes
│   ├── services/              # Business logic
│   ├── ml/                    # Machine learning models
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React application
└── README.md
```

## License

MIT
