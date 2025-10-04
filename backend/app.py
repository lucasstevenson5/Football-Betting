from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from routes.player_routes import player_bp
from routes.data_routes import data_bp
import schedule
import time
import threading
from services.nfl_data_service import NFLDataService

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for React frontend
    CORS(app)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(player_bp)
    app.register_blueprint(data_bp)

    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Football Betting API is running'
        }), 200

    return app


def run_scheduled_update(app):
    """
    Run scheduled data updates
    This runs in a separate thread to avoid blocking the main application
    """
    def job():
        with app.app_context():
            print(f"Running scheduled data update at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                NFLDataService.sync_all_data(years=5)
                print("Scheduled update completed successfully")
            except Exception as e:
                print(f"Error during scheduled update: {e}")

    # Schedule daily update at configured hour (default 6 AM)
    schedule.every().day.at(f"{Config.UPDATE_STATS_HOUR:02d}:00").do(job)

    print(f"Scheduled daily updates at {Config.UPDATE_STATS_HOUR:02d}:00")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    app = create_app()

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduled_update, args=(app,), daemon=True)
    scheduler_thread.start()
    print("Data update scheduler started")

    # Run the Flask app
    print(f"Starting Flask server on port {Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
