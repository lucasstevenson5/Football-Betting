# Football Betting Frontend

React-based frontend for displaying NFL player statistics and predictions.

## Tech Stack

- **React** 18+ with Vite
- **Axios** for API calls
- **CSS3** for styling

## Features

- 📊 Display current season NFL player stats
- 🔍 Filter by position (WR, RB, TE)
- 📈 Sort by different statistics
- 🎨 Responsive, modern UI
- ⚡ Real-time data from backend API

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:5000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── PlayerCard.jsx        # Individual player stat card
│   │   ├── PlayerCard.css
│   │   ├── PlayerList.jsx        # List of all players
│   │   └── PlayerList.css
│   ├── services/
│   │   └── api.js                # API service layer
│   ├── App.jsx                   # Main app component
│   ├── App.css
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── package.json
└── vite.config.js
```

## API Integration

The frontend connects to the backend API at `http://localhost:5000/api`.

**Endpoints used:**
- `GET /players/current-season` - Fetch current season players with filters
- `GET /players/:id` - Get specific player details
- `GET /players/:id/stats/summary` - Get player stats summary

## Components

### PlayerList
Main component that:
- Fetches players from API
- Provides filtering by position
- Allows sorting by different stats
- Displays loading/error states

### PlayerCard
Displays individual player information:
- Player name, position, team
- Current season statistics
- Receiving/rushing breakdown
- Color-coded by position

## Customization

To change the API URL, edit `src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## Features Coming Soon

- Player detail page with historical stats
- Vegas lines comparison
- ML predictions display
- Charts and graphs
- Search functionality
