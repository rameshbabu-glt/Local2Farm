"""
Local2Farm: An AI Agent for Helping Farmers Sell Their Crops
Main Application Entry Point (Flask + SQLite + AI Agent)
"""

import os
from flask import Flask, render_template, session
from config import Config
from models import db
from routes.auth import auth_bp
from routes.farmer import farmer_bp
from routes.admin import admin_bp
from data.sample_data import seed_database

def create_app():
    """Application factory for Local2Farm"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Database with app
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(admin_bp)

    # Context processor for global template variables
    @app.context_processor
    def inject_global_data():
        return {
            'user_logged_in': 'user_id' in session,
            'user_role': session.get('user_role'),
            'user_name': session.get('user_name'),
            'demo_mode': app.config.get('DEMO_MODE', True)
        }

    # Home Route
    @app.route('/')
    def home():
        return render_template('index.html')

    # Quick demo info route / modal helper
    @app.route('/about')
    def about():
        return render_template('index.html', scroll_to='about')

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', custom_body="""
            <div class="container py-5 text-center">
                <h1 class="display-4 text-success"><i class="bi bi-exclamation-triangle"></i> 404</h1>
                <h3 class="fw-bold">Page Not Found</h3>
                <p class="text-muted">The requested page could not be located.</p>
                <a href="/" class="btn btn-success mt-3"><i class="bi bi-house"></i> Return Home</a>
            </div>
        """), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', custom_body="""
            <div class="container py-5 text-center">
                <h1 class="display-4 text-danger"><i class="bi bi-bug"></i> 500</h1>
                <h3 class="fw-bold">Application Error</h3>
                <p class="text-muted">An unexpected error occurred. Please try again.</p>
                <a href="/" class="btn btn-success mt-3"><i class="bi bi-house"></i> Return Home</a>
            </div>
        """), 500

    # Auto-initialize database tables and seed sample data if not yet created
    with app.app_context():
        db.create_all()
        seed_database()

    return app

app = create_app()

if __name__ == '__main__':
    print("\n=======================================================")
    print(" Local2Farm: AI Decision Support for Farmers")
    print(" Final-Year B.Tech Project")
    print(" Web Server running on: http://127.0.0.1:5000")
    print(" Demo Farmer: ramesh@farmer.com | farmer123")
    print(" Demo Admin:  admin@local2farm.com | admin123")
    print("=======================================================\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
